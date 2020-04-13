#!/usr/bin/env python
# -*- coding:utf-8 -*-
import time
from flask import Blueprint, jsonify
from service.red_envelope.common import *
from service.red_envelope.PayAlipay import PayAlipay
from service.red_envelope.common import get_request_need_args, pay_config
from service.all_average.utils import authorization
from service.red_envelope.PayOrder import PayOrder
from service.all_average.common_sql import AllAverageSql

grab_all_average_blueprint = Blueprint('grab_all_average', __name__)


@grab_all_average_blueprint.route('/grabaa', methods=['POST'])
@authorization
def grab_aa(user_id: str = None):
    """

    :param user_id:
    :return:
    """
    json_dict = {
        "ret": 0,
        "message": "",
        "error_code": 0,
        "error_ext": "",
        "data": {
            "pay_channel": "",
            "pay_parmas": "",
            "aid": 0
        }
    }

    """
    检查用户是否符合aa资格， 不用检验是否在群内， 只要数据库里存在这个用户即可
    """

    pass

    """
    创建流水
    """
    aas = AllAverageSql()
    current_params = {
        # 公共参数
        "action": None, "group_id": "", "user_id": "",
        # 必要参数
        "aid": 0,  # "credit":0.00 先从
    }
    current_params = get_request_need_args(**current_params)
    aid = current_params.get('aid')
    if not aid:
        json_dict['error_code'] = 404
        json_dict['message'] = "没有相应的红包"
        return jsonify(json_dict)
    try:
        credit = aas.get_payment(user_id, aid)
        if not credit or credit <= 0.00:
            json_dict['error_code'] = 502
            json_dict['message'] = "aa金额出错"
            return jsonify(json_dict)

        # 如果是支付宝的取支付宝帐户
        if pay_config['pay_channel'] == "alipay":
            user_pay_info = aas.get_user_pay_alipay_account(user_id)
            pay_account = user_pay_info['alipay_login_account']
            # pay_account = "simulator_account_02"
            if len(pay_account) == 0:  # TODO 这里len可能会出错
                json_dict['message'] = "用户没有绑定支付宝帐户"
                json_dict['error_ext'] = "alipay_login_account"
                return jsonify(json_dict)
        else:
            # 其他支付方式 在取
            user_pay_info = {""}
            pay_account = ""
            pass

        # 创建订单
        format_order_params = {
            "aid": aid,
            "order_type": "all_average",
            "pay_channel": pay_config['pay_channel'],
            "pay_account": pay_account,
            "credit": str(credit),
            # "remain_credit": 0.00,
            "create_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "order_comments": {}
        }
        po = PayOrder(**format_order_params)

        # today_pay = po.get_user_today_pay_red_envelope()
        # if (today_pay + current_params['credit']) > pay_config['all_average']['day_pay_credit_limit']:
        #     json_dict['message'] = "已达到单日支付限额"
        #     json_dict['error_ext'] = "credit"
        #     return jsonify(json_dict)

        order_result = po.create()
        if order_result['ret'] != 1:
            json_dict['error_code'] = order_result['error_code']
            json_dict['message'] = "支付aa失败"
            return jsonify(order_result)
        order_no = po.get_order_no()
        # 创建aa支付流水
        order_id = order_result["data"]["id"]
        # order_no = order_result["data"]["no"]

        # 缓存红包信息
        # aas.cache_red_info(aid)
        # 有红包id了， 有订单id ,生成订单流水
        trace_result = po.insert_order_trace()

        if trace_result['ret'] != 1:
            json_dict['error_code'] = trace_result['error_code']
            json_dict['message'] = "创建红包失败"
            return jsonify(json_dict)
        order_line = trace_result['data']['order_line']
        # 订单流水用于 生成支付链接参数
        # 创建红包成功后 生成支付信息， 订单流水

        ret = aas.update_payer_order(aid, user_id, order_id, order_line)
        if not ret:
            json_dict['error_code'] = 500
            json_dict['message'] = "更新用户信息失败"
            return jsonify(json_dict)
        if pay_config['pay_channel'] == "alipay":
            pa = PayAlipay()
            pay_params = pa.get_app_pay(order_no=order_no, amount=credit, alipay_uid=pay_account,
                                        title=pay_config['all_average']['bill_title'])
            json_dict['ret'] = 1
            json_dict['error_code'] = 200
            json_dict['message'] = "获取aa成功"
            json_dict['data']['pay_channel'] = pay_config['pay_channel']
            json_dict['data']['pay_parmas'] = pay_params
            json_dict['data']['aid'] = aid
            return jsonify(json_dict)
        else:
            # 其他支付方式 在取
            json_dict['error_code'] = 4023
            json_dict['message'] = "不支持的支付方式"
            return jsonify(json_dict)

    except Exception as e:
        json_dict['error_code'] = e
        if not is_int(json_dict['error_code']):
            print("all_average", "aa id:%s出错%s" % (0, json_dict['error_code']))
            json_dict['error_code'] = 0

        json_dict['message'] = "支付aa失败!"
        json_dict['error_ext'] = ""
        return jsonify(json_dict)
