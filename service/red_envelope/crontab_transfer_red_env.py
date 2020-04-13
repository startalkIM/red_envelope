#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
定时脚本，已抢到的红包转帐
转帐超过红包过期时间 +1分钟将不在转帐(如果超过了需要报警处理),红包退款时间 是红包过期时间+5分钟

"""
import os
import sys

# 增加system path 以便获取对应的自定义包
sys.path.append(os.path.abspath(os.path.dirname(__file__)+"/../../"))
from service.red_envelope.common import *

from service.red_envelope.common_sql import RedEnvelopeSql
from service.red_envelope.PayOrder import PayOrder
from service.red_envelope.PayAlipay import PayAlipay
from utils.send_qtalk_message_utils import QtalkMessage

from service.red_envelope.crontab_common import RedEnvCrontab

r_log = configure_logger("red_envelope_transfer")


# 判断程序是否正在运行，没有运行打上pid标记
is_run = RedEnvCrontab.crontab_run_begin(__file__)

if is_run:
    r_log.info("is_run")
    sys.exit("程序正在执行")

r_log.info("开始执行红包转账脚本～")

pa = PayAlipay()
rels = RedEnvelopeSql()
pg_cursor = rels.get_pg_dict_cursor()

"""
发送qtalk 消息
"""


def send_error_message(msg):
    user = []
    for i in pay_config['alert_user_id']:
        user.append({"user": i, "host": r_domain[0]})

    params = {
        "from": "crontab_transfer_red_env",
        "fromhost": r_domain[0],
        "to": user,
        "content": msg,
        "extendinfo": ""
    }
    return QtalkMessage.send(1, **params)




sql = """select 
            re.id as red_id,re.order_id,re.expire_time,re.expire_time+'1m' as expire_time
            ,ol.pay_channel,ol.pay_account
            ,redr.id,redr.host_id,redr.user_id,redr.credit::float,redr.draw_time
            ,to_char(redr.draw_time,'YYYYMMDDHH24MISS') as draw_time_str
            ,hupa.alipay_login_account
            from 
            public.red_envelope_draw_record as redr
            join public.red_envelope as re on redr.red_envelope_id=re.id
            join public.order_list as ol on re.order_id = ol.id 
            join public.host_users_pay_account as hupa on redr.host_id = hupa.host_id and redr.user_id = hupa.user_id
            where redr.has_transfer=0 and transfer_order_line is null and redr.user_id is not null
            and ol.state='pay'
            and now() < re.expire_time+'1m'
            order by redr.id asc 
        """

pg_cursor.execute(sql)
while True:
    row = pg_cursor.fetchone()
    if row is None:
        r_log.info("无转账红包～")
        break
    pg_cursor_normal = rels.get_pg_cursor()
    row['expire_time'] = row['expire_time'].strftime("%Y-%m-%d %H:%M:%S")
    row['credit'] = float(row['credit'])

    """
    1、拿到记录 ，验证订单金额
    2、生成新的红包对应的 转帐 order_trace  order_line
    3、更新red_envelope_draw_record
    4、调用支付打款
    """
    message_prefix = "红包id:%s;小红包id:%s;订单id:%s;支付方式:%s;" % (row['red_id'], row['id'], row['order_id'], row['pay_channel'])

    r_log.info(message_prefix + "开始转帐")

    if row['pay_channel'] != "alipay":
        # 其他支付方式
        continue

    try:

        po = PayOrder(id=row['order_id'])

    except Exception as e:
        if str(e) == '2001':
            message = message_prefix+"\n红包转账出错;\n订单不存在，不转帐"
            send_error_message(message)
            r_log.error(message)
        continue

    r_log.info(message_prefix + "当前红包余额%s" % po.get_remain_credit())

    # 减去当前小红包，所剩余额
    remain_credit = decimal_2_float(po.get_remain_credit() - row['credit'])

    if po.get_remain_credit() <= 0 or remain_credit < 0:
        message = message_prefix + "\n红包转账出错;\n红包剩余金额%s,待转账金额为%s;余额不足" % (po.get_remain_credit(), row['credit'])
        send_error_message(message)
        r_log.error(message)
        continue

    order_trace_result = po.insert_order_trace(**{
            "op": "return_balance",
            "order_line": po.generate_sub_red_envelope_order_no(sub_red_envelope_id=row['id'], draw_time_str=row['draw_time_str']),
            "credit": row['credit'],
            "pay_status": "re_balance_ing",
            'trace_comments': {
                 "red_envelope_draw_record_id": row['id'],
                 "credit": row['credit']
             }
         })

    if order_trace_result['ret'] != 1:
        message = message_prefix + "\n红包转账出错;\n生成order_trace记录失败;"
        send_error_message(message)
        r_log.error(message)
        continue

    # 生成订单流水
    order_line = order_trace_result['data']['order_line']
    message = message_prefix + "订单流水order_line:%s" % order_line
    r_log.info(message)

    pg_cursor_normal.execute('begin')
    try:
        # 更新小红包转帐状态
        r_sql = """UPDATE public.red_envelope_draw_record 
                        SET has_transfer=1, transfer_order_line=%(order_line)s, transfer_time=current_timestamp
                        WHERE id=%(id)s and has_transfer=0 and transfer_order_line is null
                        RETURNING  id
                    """

        pg_cursor_normal.execute(r_sql, {"order_line": order_line, "id": row['id']})
        update_result = pg_cursor_normal.fetchone()
        if not update_result[0]:
            # 更新失败了
            pg_cursor_normal.execute("rollback")
            message = message_prefix + "\n数据操作失败，更新red_envelope_draw_record失败，请检查日志\n" % (json.dumps(disburse_result))
            send_error_message(message)
            r_log.error(message)
            continue

        # 更新订单的余额
        o_sql = """UPDATE public.order_list 
                    SET remain_credit=%(remain_credit)s where id=%(id)s and remain_credit=%(old_remain_credit)s
                """
        pg_cursor_normal.execute(o_sql, {"remain_credit": remain_credit,
                                         'old_remain_credit': po.get_remain_credit(),
                                         "id": row['order_id']})
        statusmessage = parse_psycopg2_statusmessage(pg_cursor_normal.statusmessage)
        if str(statusmessage) != "1":
            # 更新失败了
            message = message_prefix + "\n数据操作失败，更新orer_list失败\nstatusmessage:%s;sql:%s" \
                      % (statusmessage, pg_cursor_normal.query)
            send_error_message(message)
            r_log.error(message)
            pg_cursor_normal.execute("rollback")
            continue
        # 主动提交事务
    except Exception as e:
        error_info = str(e)
        pg_cursor_normal.execute("rollback")
        message = message_prefix + "\n处理小红包转帐异常，错误如下:\n%s" % error_info
        send_error_message(message)
        r_log.error(message)
        continue

    # 是支付宝支付 BGN
    r_log.info(message_prefix + "调用alipay开始")
    disburse_result = pa.disburse(
        order_no=order_line,
        original_order_id=po.get_pay_order_no(),
        amount=row['credit'],
        payee_logon_id=row['alipay_login_account'],
        title=pay_config['red_envelope']['grab_bill_title']
        )
    r_log.info(message_prefix + "调用alipay结束并返回:" + json.dumps(disburse_result, ensure_ascii=False))

    # 支付失败了
    if not disburse_result['ret']:
        pg_cursor_normal.execute("rollback")
        message = message_prefix + "\n红包领取转账失败;\n返回结果:%s" % (json.dumps(disburse_result, ensure_ascii=False))
        send_error_message(message)
        r_log.error(message)

        # 更新order_trace表

        order_trace_result = po.insert_order_trace(**{
            "order_line": order_line,
            "op": "return_balance",
            "credit": row['credit'],
            "pay_order_no": "",
            "pay_status": "re_balance_faild",
            'trace_comments': disburse_result
        })
        continue

    # 更新order_trace表

    order_trace_result = po.insert_order_trace(**{
        "order_line": order_line,
        "op": "return_balance",
        "credit": row['credit'],
        "pay_order_no": disburse_result['order_id'],
        "pay_status": "re_balance_ok",
        'trace_comments': disburse_result
    })
    pg_cursor_normal.execute("commit")
    if order_trace_result['ret'] != 1:
        message = message_prefix + "\n红包调用支付宝成功，插入order_trace失败，order_line:%s;请检order_list日志" % order_line
        send_error_message(message)
        r_log.error(message)
        continue

    r_log.info(message_prefix + "插入order_trace成功")

    # 是支付宝支付 END
RedEnvCrontab.crontab_run_done(__file__)
r_log.info("执行完成")
