#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
定时脚本，红包过期退款
红包退款时间 红包过期时间+5分钟, 5小时内未退款则发qtalk提醒，不在执行退款操作. 支付宝退款是48小时
"""

import os
import sys
import time

# 增加system path 以便获取对应的自定义包
sys.path.append(os.path.abspath(os.path.dirname(__file__)+"/../../"))
from service.red_envelope.common import *

from service.red_envelope.common_sql import RedEnvelopeSql
from service.red_envelope.RedEnvelope import RedEnvelope
from service.red_envelope.PayOrder import PayOrder
from service.red_envelope.PayAlipay import PayAlipay
from utils.send_qtalk_message_utils import QtalkMessage

from service.red_envelope.crontab_common import RedEnvCrontab

r_log = configure_logger("red_envelope_refund")

# 判断程序是否正在运行，没有运行打上pid标记
is_run = RedEnvCrontab.crontab_run_begin(__file__)
if is_run:
    r_log.info("is_run")
    sys.exit("程序正在执行")

"""
发送qtalk 消息
"""

def send_error_message(msg):
    user = []
    for i in pay_config['alert_user_id']:
        user.append({"user": i, "host": r_domain[0]})

    params = {
        "from": "crontab_refund_red_env",
        "fromhost": r_domain[0],
        "to": user,
        "content": msg,
        "extendinfo": ""
    }
    return QtalkMessage.send(1, **params)



r_log.info("开始执行退红包剩余金额脚本~")


pa = PayAlipay()
rels = RedEnvelopeSql()

re = RedEnvelope()
pg_cursor = rels.get_pg_dict_cursor()
redis_cli = rels.get_redis_conn()


# 红包过期时间+5分钟

sql = """SELECT re.id as red_id, re.order_id, re.balance,re.expire_time
            ,to_char(re.create_time,'YYYYMMDDHH24MISS') as create_time_str
            ,ol.pay_channel,ol.pay_account
        FROM public.red_envelope as re
        JOIN public.order_list as ol on re.order_id=ol.id 
        WHERE  re.expire_time < current_timestamp+'-5m'
        and re.draw_number < re.red_number 
        and re.balance>0 
        and ol.order_type='red_envelope' and ol.state='pay' and ol.remain_credit>0
        order by re.id asc
"""

pg_cursor.execute(sql)
while True:
    current = pg_cursor.fetchone()
    if current is None:
        r_log.info("没有需要退款的红包～")
        break
    pg_cursor2 = rels.get_pg_dict_cursor()
    row = {}
    row['expire_time'] = current['expire_time'].strftime("%Y-%m-%d %H:%M:%S")
    # 退款超时时间为5小时，5小时未退款发qtalk消息(一天内只提醒一次)
    row['expire_timestamp'] = int(time.mktime(current['expire_time'].timetuple())) + 5*60*60
    row['balance'] = float(current['balance'])
    row['order_id'] = int(current['order_id'])
    row['red_id'] = int(current['red_id'])
    row['pay_channel'] = str(current['pay_channel'])
    row['create_time_str'] = str(current['create_time_str'])

    """
    1、拿到记录 ，验证订单金额
    2、生成新的红包对应的 转帐 order_trace  order_line
    3、插入退款表 state= new 
    4、调用退款，
    5、更新 order表为已退款， +退款金额， 剩余金额更改为0
    5、更新退款表为done
    """
    message_prefix = "红包id:%s;订单id:%s;支付方式:%s;待退款金额:%s;" \
                     % (row['red_id'], row['order_id'], row['pay_channel'], row['balance'])

    r_log.info(message_prefix + "开始退款流程")

    # 必须是支付宝退款的才执行本程序
    if row['pay_channel'] != "alipay":
        # 其他支付方式
        r_log.info(message_prefix + "不是支付宝方式付款，不进行退款操作")
        continue

    # 判断是否退款超时

    if row['expire_timestamp'] < time.time():
        # 退款超时了。不在进行退款操作
        message = message_prefix + "\n退款超时了。不在进行退款操作，请对应红包是否已退款"
        r_log.info(message)

        balance_timeout_redis_key = re.get_redis_key(row['red_id'], "balance_timeout")
        is_send = redis_cli.get(balance_timeout_redis_key)
        if is_send:
            continue

        send_error_message(message)
        redis_cli.set(balance_timeout_redis_key, "1")
        # 一天内有效
        redis_cli.expire(balance_timeout_redis_key, 86400)
        continue
    try:
        po = PayOrder(id=row['order_id'])
    except Exception as e:
        message = message_prefix+"\n红包退款出错;\n获取订单信息失败，未执行退款操作;%s" % str(e)
        send_error_message(message)
        r_log.error(message)
        continue

    refund_credit = po.get_refund_credit()

    if po.get_state() != 'pay':
        if refund_credit > 0.0:
            message = message_prefix + "红包已退款;退款金额%s" % refund_credit
        else:
            message = message_prefix + "不能执行退款操作，订单状态:%s" % po.get_state()
        r_log.error(message)
        continue

    need_refund_credit = po.get_remain_credit()

    message = message_prefix + "需退款金额:%s" % need_refund_credit

    if need_refund_credit < 0.0:
        # 无退款金额
        continue

    r_log.error(message)

    order_trace_result = po.insert_order_trace(**{
        "op": "refund",
        "order_line": po.generate_refund_order_no(create_time_str=row['create_time_str']),
        "credit": need_refund_credit,
        "pay_status": "refund_ing",
        'trace_comments': {
            "credit": need_refund_credit
        }
    })

    if order_trace_result['ret'] != 1:
        message = message_prefix + "\n红包退款出错;\n生成order_trace记录失败;"
        send_error_message(message)
        r_log.error(message)
        continue

    # 生成订单流水
    order_line = order_trace_result['data']['order_line']
    message = message_prefix + "订单流水order_line:%s" % order_line
    r_log.info(message)

    # 判断 是否已进行转帐

    # 一个红包 且 仅只有一条退款数据
    refund_data_sql = """SELECT * FROM public.red_envelope_refund_handled_data 
            WHERE order_id=%(order_id)s and state='new' order by id desc limit 1"""
    pg_cursor2.execute(refund_data_sql, {"order_id": row['order_id']})
    refund_handled_data = pg_cursor2.fetchone()

    if not refund_handled_data:
        refund_data_sql = """INSERT into public.red_envelope_refund_handled_data(order_id, refund_money,state) 
                VALUES (%(order_id)s, %(refund_money)s, 'new') RETURNING id"""
        pg_cursor2.execute(refund_data_sql, {"order_id": row['order_id'], "refund_money": need_refund_credit})
        refund_handled_data = pg_cursor2.fetchone()
        if not refund_handled_data["id"]:
            message = message_prefix + "插入 refund_handled_data失败\nstatusmessage:%s;sql:%s" \
                      % (pg_cursor2.statusmessage, pg_cursor2.query)
            send_error_message(message)
            r_log.error(message)
            pg_cursor2.execute("rollback")
            continue



    # 发起支付宝退款
    r_log.info(message_prefix + "调用alipay开始")

    refund_result = pa.refund(
        request_no=order_line,
        order_id=po.get_pay_order_no(),
        amount=need_refund_credit)

    r_log.info(message_prefix + "调用alipay结束并返回:" + json.dumps(refund_result, ensure_ascii=False))

    # 支付失败了
    if not refund_result['ret']:

        pg_cursor2.execute("rollback")
        message = message_prefix + "\n调用alipay红包退款失败，执行回滚操作;\n返回结果:%s" % (json.dumps(refund_result, ensure_ascii=False))
        send_error_message(message)
        r_log.error(message)
        # 更新order_trace表

        order_trace_result = po.insert_order_trace(**{
            "order_line": order_line,
            "op": "refund",
            "credit": need_refund_credit,
            "pay_status": "refund_faild",
            'trace_comments': {
                "credit": need_refund_credit,
                "refund_result": refund_result
            }
        })
        continue

    # 订单退款状态 如果是 全额退，则是 refund 否则是 partial_refund
    refund_state = "partial_refund" if need_refund_credit != po.get_credit() else "refund"

    pg_cursor2.execute("begin")

    # 更新订单剩余金额为0,
    o_sql = """UPDATE public.order_list SET 
    remain_credit=0.0,refund_time=current_timestamp 
    ,state = %(state)s
    ,refund_order_line=%(order_line)s,refund_credit=%(refund_credit)s
    where id=%(id)s and remain_credit=%(refund_credit)s and state='pay'"""

    pg_cursor2.execute(o_sql,
                       {
                        "state": refund_state,
                        "order_line": order_line,
                        "refund_credit": need_refund_credit,
                        "id": row['order_id'],
                        })
    statusmessage = parse_psycopg2_statusmessage(pg_cursor2.statusmessage)
    if str(statusmessage) != "1":
        # 更新失败了
        message = message_prefix + "\n数据操作失败，更新orer_list失败\nstatusmessage:%s;sql:%s" \
                  % (statusmessage, pg_cursor2.query)
        send_error_message(message)
        r_log.error(message)
        pg_cursor2.execute("rollback")
        continue

    rhd_sql = "update public.red_envelope_refund_handled_data set state='done' where id=%(id)s RETURNING id"

    pg_cursor2.execute(rhd_sql, {"id": refund_handled_data["id"]})
    statusmessage = parse_psycopg2_statusmessage(pg_cursor2.statusmessage)
    if str(statusmessage) != "1":
        # 更新失败了
        message = message_prefix + "\n数据操作失败，更新refund_handled_data失败\nstatusmessage:%s;sql:%s" \
                  % (statusmessage, pg_cursor2.query)
        send_error_message(message)
        r_log.error(message)
        pg_cursor2.execute("rollback")
        continue

    # 主动提交事务
    pg_cursor2.execute("commit")

    order_trace_result = po.insert_order_trace(**{
        "order_line": order_line,
        "op": "refund",
        "credit": need_refund_credit,
        "pay_status": "refund_ok",
        'trace_comments': {
            "credit": need_refund_credit,
            "refund_result": refund_result
        }
    })

    if order_trace_result['ret'] != 1:
        message = message_prefix + "\n红包退款出错;\n生成order_trace记录失败;"
        send_error_message(message)
        r_log.error(message)
        continue

RedEnvCrontab.crontab_run_done(__file__)
r_log.info("执行完成")
