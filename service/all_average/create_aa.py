#!/usr/bin/env python
# -*- coding:utf-8 -*-
import time
from flask import Blueprint, jsonify
from service.all_average.params_check import check_params
from service.all_average.common_sql import AllAverageSql
from service.all_average.AllAverage import AllAverage
from service.red_envelope.common import authorization, get_request_need_args, pay_config
from service.red_envelope.PayOrder import PayOrder
from service.red_envelope.common_sql import *
from utils.send_qtalk_message_utils import *
from utils.aa_rounding import cal_avg_credit

create_all_average_blueprint = Blueprint('create_all_average', __name__)

"""
创建aa， 需要
1. 创建aa表相关的数据 包括：创建时间、 {
        # 公共参数
        "action": None, "group_id": None, "user_id": None,
        # aa参数
        "credit": 0.00, "number": 0.00, "atype": '', "detail": [], 'content': ''
    }
2. 给每个付款人创建aa付款表对应的初始化条目
3. 发送消息给当前群
4. 当一个人打开aa时候， 首先检查各种状态， 从aa表获取aa信息
5. 付款， 当后台的反馈接口成功之后， 更新付款表和aa表， 并且加入redis队列
6. crontab付款

每一个aa，需要一个id， 对应了
"""

if len(r_domain) > 1:
    print("注意! domain数量大于1")
_domain = r_domain[0]
con_domain = "conference." + _domain


@create_all_average_blueprint.route('/createaa', methods=['POST'])
@authorization
def create_aa(user_id: str = None):
    """
    返回参数
    """
    json_dict = {"ret": 0, "message": "", "error_code": 0, "error_ext": "", "data": {}}

    """
    检查用户ckey
    """
    if user_id == 'DEFAULT' or user_id is None or len(str(user_id)) == 0:
        json_dict['message'] = "未登录用户"
        json_dict['user_id'] = user_id
        return jsonify(json_dict)

    """
    检查参数， 获取必要变量
    """
    current_params = {
        # 公共参数
        "action": None, "group_id": None, "user_id": None,
        # 红包参数
        "credit": 0.00, "number": 0.00, "atype": '', "detail": [], 'content': ''

    }

    if isinstance(current_params.get('number'), str):
        current_params['number'] = int(current_params['number'])

    current_params = get_request_need_args(**current_params)
    check_result = check_params(current_params)
    if check_result["ret"] != 1:
        json_dict['message'] = check_result["err_msg"]
        json_dict['user_id'] = user_id
        return jsonify(json_dict)
    """
    创建order_list, 获取order_id
    """
    aa_type = current_params['atype']
    aas = AllAverageSql()

    # aa目前没有支付上限
    # today_pay = po.get_user_today_pay_red_envelope()
    #
    # if (today_pay + current_params['credit']) > pay_config['red_envelope']['day_pay_credit_limit']:
    #     json_dict['message'] = "已达到单日支付限额"
    #     json_dict['error_ext'] = "credit"
    #     return jsonify(json_dict)

    # order_id = order_result["data"]['id']
    # order_no = po.get_order_no()
    # 为aa计算每个人的金额
    details = current_params['detail']
    numbers = int(current_params['number'])
    credit = float(current_params['credit'])
    aa_money = 0
    if aa_type == 'normal':
        aa_money = cal_avg_credit(num=numbers, credit=credit)
        if not aa_money:
            json_dict['message'] = "参数有误"
            json_dict['user_id'] = user_id
            return jsonify(json_dict)
        for _u in details:
            details[_u] = aa_money

    """
    创建aa
    """
    # 创建订单
    rels = RedEnvelopeSql()

    format_params = {
        "host_id": aas.host_id,
        "user_id": user_id,
        # "order_id": order_id,
        "number": numbers,
        "credit": credit,
        # "balance": current_params['credit'],
        "aa_type": aa_type,
        "aa_number": numbers,
        "amount": 0,
        "paid_number": 0,
        "aa_content": current_params['content'],
        "group_chat_id": current_params['group_id'],
        "create_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "expire_time": time.strftime("%Y-%m-%d %H:%M:%S",
                                     time.localtime(time.time() + pay_config['all_average']['expiry_time'])),
        "members": list(details.keys()),
        "details": details,
        "avg_money": 0
    }
    avg_money = cal_avg_credit(num=format_params.get('aa_number'), credit=format_params.get('credit'))
    format_params["avg_money"] = avg_money

    if user_id + '@' + _domain in details.keys():
        # format_params["details"].pop(user_id + '@' + _domain)
        format_params["paid_number"] += 1
        format_params["amount"] += avg_money

    # aa = AllAverage(**format_params)
    # aa_result = aa.create()

    payee_account = rels.get_user_pay_alipay_account(user_id).get('alipay_login_account')
    # payee_account = "simulator_account_01"
    if not payee_account:
        # 红包不存在　
        json_dict['error_code'] = 4300
        json_dict['error_ext'] = "user"
        json_dict['message'] = "用户未绑定支付宝"
        return display_json(json_dict)
    if rels.get_alipay_account_is_bind(user_id, payee_account):
        json_dict['error_code'] = 500
        json_dict['message'] = "用户支付宝账户已绑定"
        return display_json(json_dict)

    format_params['payee_account'] = payee_account
    aa_id = aas.create_all_average(format_params)  # 创建aa几其从属的子aa
    if not aa_id:
        return False

    """通知payer付款"""
    to_muc = current_params['group_id']
    if '@' in to_muc:
        to_muc = to_muc.split('@')[0]
    params = {
        "from": user_id,
        "fromhost": _domain,
        "to": [{"user": to_muc, "host": con_domain}],
        "content": "aa支付",
        "type": "groupchat",
        "extendinfo": {
            "aid": str(aa_id),  # 红包id
            "type": current_params["atype"],  # 红包类型， normal=普通红包,lucky=拼手气
            "content": current_params["content"],  # 红包内容
            # "money": 0.00 可以把用户需要收多少钱放到这里
        }
    }
    if current_params["atype"] == 'normal':
        params["extendinfo"]["total"] = str(current_params["credit"])
        params["extendinfo"]["person_num"] = str(numbers)
        params["extendinfo"]["avg_money"] = str(aa_money)
    elif current_params["atype"] == 'custom':
        params["extendinfo"]["total"] = str(current_params["credit"])
        params["extendinfo"]["person_num"] = str(numbers)
        params["extendinfo"]["detail"] = details

    qtalk_message = QtalkMessage()
    print("准备请求发送消息: 时间 {} 参数 {}".format(time.time(), params))
    ret = qtalk_message.send(513, **params)
    if not ret:
        json_dict['error_code'] = 500
        json_dict['error_ext'] = "qtalk"
        json_dict['message'] = "发送qtalk消息失败"
        return display_json(json_dict)

    print("发送消息请求结束: 时间 {} 返回 {}".format(time.time(), ret))
    """返回"""
    json_dict['ret'] = 1
    json_dict['error_code'] = 200
    json_dict['message'] = "初始化aa成功"
    json_dict['data']['pay_channel'] = pay_config['pay_channel']
    json_dict['data']['aid'] = aa_id
    return jsonify(json_dict)
