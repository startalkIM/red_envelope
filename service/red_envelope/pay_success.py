#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
支付宝红包异步回调
https://docs.open.alipay.com/204/105301/
红包支付成功回调
回调
https://docs.alipay.com/mini/introduce/redpacket

@author meijie.ge
@date 2019-06-14
"""

from service.red_envelope.common import *

from service.red_envelope.PayAlipay import PayAlipay
from service.red_envelope.PayOrder import PayOrder
from service.red_envelope.RedEnvelope import RedEnvelope
from service.red_envelope.common_sql import RedEnvelopeSql
from service.all_average.common_sql import AllAverageSql
from utils.logger_conf import configure_logger
from utils.request_util import RequestUtil
from utils.send_qtalk_message_utils import QtalkMessage
import traceback

pay_success_blueprint = Blueprint('pay_success', __name__)


@pay_success_blueprint.route('/pay_success', methods=['POST', 'GET'])
def pay_success():
    current_args = RequestUtil.get_request_args(request)
    logger = configure_logger("pay_success")
    logger.info("支付回调接口参数：" + json.dumps(current_args))

    # 测试的时候暂不验签
    pa = PayAlipay()
    status = pa.check_sign(**current_args)
    if not status:
        logger.info("验签失败")
        return "fail"

    # 商家的appid
    app_id = current_args['app_id']

    if app_id != pay_config['appId']:
        logger.info("appid校验失败")
        return "fail"
    # 如果不是支付回调  直接返回fail
    if current_args['msg_method'] != 'alipay.fund.trans.order.changed':
        logger.info("msg_method 不是 alipay.fund.trans.order.changed")
        return "fail"

    current_args = json.loads(current_args['biz_content'])
    '''
        {
        "action_type": "FINISH",
        "biz_scene": "PERSONAL_PAY",
        "order_id": "20190912110075000006740023648562", #支付宝系统的单据唯一ID
        "origin_interface": "alipay.fund.trans.app.pay", #支付的接口
        "out_biz_no": "qt_20190912162507_298",#商户端的唯一订单号
        "pay_date": "2019-09-12 16:25:15", 
        "pay_fund_order_id": "20190912110075001506740023416000",#支付宝支付资金流水号（转账成功时才返回）
        "product_code": "STD_RED_PACKET",
        "status": "SUCCESS",
        "trans_amount": "0.01"
    }
    '''
    # 只有成功的 才进行下一部
    if current_args['status'] != 'SUCCESS':
        logger.info("本次status：%s ,直接返回success" % current_args['status'])
        return "success"

    # 支付宝交易号
    pay_order_no = current_args['order_id']
    pay_order_line = current_args['pay_fund_order_id']
    # 商家唯一订单号
    out_order_no = current_args['out_biz_no']

    # 支付金额
    amount = float(current_args['trans_amount'])

    # 付款时间
    gmt_payment = current_args['pay_date']

    red_instance = RedEnvelopeSql()
    conn = red_instance.get_pg_conn()
    pg_cursor = red_instance.get_pg_dict_cursor()
    sql = "Select id,state,order_type,credit from public.order_list where order_no=%s"
    try:
        pg_cursor.execute(sql, (out_order_no,))
        row = pg_cursor.fetchone()
        conn.commit()
    except Exception as e:
        pg_cursor.close()
        logger.info("订单号order_no为:%s,数据库执行失败" % out_order_no)
        return "fail"

    if not row:
        pg_cursor.close()
        logger.info("订单未查找成功，订单号order_no为%s" % out_order_no)
        return "fail"

    if row['state'] != 'unpay':
        pg_cursor.close()
        logger.info("订单未查找成功，订单号order_no为%s;订单状态为%s，不在进行操作" % (out_order_no, row['state']))

        if row['state'] == 'pay':
            return "success"
        return "fail"

    if row['order_type'] != 'red_envelope' and row['order_type'] != 'all_average':
        pg_cursor.close()
        logger.info("订单未查找成功，订单号order_no为%s;订单状态为%s，order_type:%s;直接退出" % (out_order_no, row['order_type']))
        return "fail"

    if amount != float(row['credit']):
        pg_cursor.close()
        logger.info("支付金额与订单金额不符，支付金额 %s  VS  订单金额 %s" % (amount, row['credit']))
        return "fail"

    # 修改订单状态﻿
    # auth_no:pay_order_no
    # out_order_no:order_no
    # operation_id:pay_order_line
    # out_request_no:order_line
    # 插入订单流水

    try:
        order_sql = """Update public.order_list set state='pay', pay_order_no=%(pay_order_no)s,pay_order_line=%(pay_order_line)s, pay_time=%(gmt_payment)s
        where order_no=%(out_order_no)s and state='unpay'"""

        pg_cursor.execute(order_sql,
                          {"pay_order_no": pay_order_no, "pay_order_line": pay_order_line, "gmt_payment": gmt_payment,
                           "out_order_no": out_order_no})
        if 0 == parse_psycopg2_statusmessage(pg_cursor.statusmessage):
            pg_cursor.close()
            logger.info("订单未查找成功，订单号order_no为%s;更新失败" % out_order_no)
            return "fail"
        conn.commit()
    except Exception as e:
        pg_cursor.close()
        logger.info("订单号order_no为%s;更新成为pay状态失败" % out_order_no)
        return "fail"

    pay_order = PayOrder(id=row['id'])
    order_trace_result = pay_order.insert_order_trace(order_line=out_order_no)

    # 生成小红包
    if row['order_type'] == 'red_envelope':
        try:
            rel = RedEnvelope(order_id=row['id'])
        except Exception as e:
            logger.info("订单号order_no为%s;红包不存在;error_code:%s" % (out_order_no, str(e)))
            return "fail"

        ret = rel.generate_sub_redenv()
        if not ret['ret']:
            return jsonify({"ret": False, "error_msg": "红包生成失败"})

        # 发送红包消息
        params = {"msg_type": "pay_success", "id": rel.id, "group_id": rel.group_chat_id[0]}
        rel.add_qtalk_message_queue(**params)
    elif row['order_type'] == 'all_average':
        try:
            aas = AllAverageSql()
            ret = aas.pay_success_callback(order_no=out_order_no, )
            if not ret:
                print("aa状态数据库更新失败")
                return 'failed'

            pa = PayAlipay()
            payee_info = aas.get_aa_payee(order_no=out_order_no)
            print("获取 支付者信息 {}".format(payee_info))
            order_line = order_trace_result['data']['order_line']
            print("准备支付")
            print("...original order id: {}".format(pay_order.get_pay_order_no()))
            print("...order_no: {}".format(order_line))
            print("...payee_info: {}".format(payee_info))

            disburse_result = pa.disburse(
                order_no=str(order_line),
                original_order_id=str(pay_order.get_pay_order_no()),
                amount=float(row['credit']),
                payee_logon_id=str(payee_info),
                title=pay_config['all_average']['grab_bill_title']
            )
            print("支付返回 {}".format(disburse_result))
            if not disburse_result['ret']:
                print("支付失败, 没有拿到返回, 结果 {}".format(disburse_result))
                # pg_cursor_normal.execute("rollback")
                # message = message_prefix + "\n红包领取转账失败;\n返回结果:%s" % (json.dumps(disburse_result, ensure_ascii=False))
                # 更新order_trace表

                order_trace_result = pay_order.insert_order_trace(**{
                    "order_line": order_line,
                    "op": "return_balance",
                    "credit": float(row['credit']),
                    "pay_order_no": "",
                    "pay_status": "re_balance_faild",
                    'trace_comments': disburse_result
                })
            else:
                order_trace_result = pay_order.insert_order_trace(**{
                    "order_line": order_line,
                    "op": "return_balance",
                    "credit": float(row['credit']),
                    "pay_order_no": disburse_result['order_id'],
                    "pay_status": "re_balance_ok",
                    'trace_comments': disburse_result
                })
            if order_trace_result['ret'] != 1:
                print("插入失败")
                print("\n红包调用支付宝成功，插入order_trace失败，order_line:%s;请检order_list日志" % order_line)
        except Exception as e:
            print(e)
            print(traceback.print_exc())
            print("aa状态更新失败")
            return "failed"
    return "success"
