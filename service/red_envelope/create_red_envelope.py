#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
/red_envelope/create
创建红包,第一步
返回 需要支付的类型，以及生成的订单的跳转信息
页面响应 post json 格式
"""
import time

from service.red_envelope.common import *

from service.red_envelope.common_sql import RedEnvelopeSql
from service.red_envelope.RedEnvelope import RedEnvelope
from service.red_envelope.PayOrder import PayOrder
from service.red_envelope.PayAlipay import PayAlipay

create_red_envelope_blueprint = Blueprint('create_red_envelope', __name__)


@create_red_envelope_blueprint.route('/create', methods=['POST', 'GET'])
@authorization
def current(user_id=None):
    json_dict = {"ret": 0, "message": "", "error_code": 0, "error_ext": "",
                 "data": {"pay_channel": "", "pay_parmas": "", "rid": 0}}

    if user_id == 'DEFAULT' or user_id is None or len(str(user_id)) == 0:
        json_dict['message'] = "未登录用户"
        json_dict['user_id'] = user_id
        return display_json(json_dict)

    # 本页面 必要参数
    """
    公共参数
    action 必须是 create_red_envelope
    group_id 红包所在群id e68c88425a4745b5af9e7a9e7465df08@conference.ejabhost1 特殊可选 group_id 与user_id 必选其1
    user_id 收红包的人 suozhu.li@ejabhost1
    红包参数
    number 红包数量
    rtype 红包类型 normal=普通红包|lucky=拼手气红包
    content 红包显示的内容
    """

    current_params = {
            # 公共参数
            "action": None, "group_id": "", "user_id": "",
            # 红包参数
            "number": 0, "credit": 0.00, "rtype": 'normal', "content": ""
            }
    # 获取本页面必要参数
    current_params = get_request_need_args(**current_params)
    # 创建红包 current_params['user_id'] 会被覆盖成当前登录用户
    rels = RedEnvelopeSql()
    rels.write_error_log("red_envelope", "建红包原始参数:%s" % (json.dumps(current_params)))

    if not is_int(current_params['number']):
        json_dict['error_ext'] = "id"
        json_dict['message'] = "参数错误"
        return display_json(json_dict)

    if not is_float(current_params['credit']):
        json_dict['error_ext'] = "credit"
        json_dict['message'] = "参数错误"
        return display_json(json_dict)

    current_params['number'] = int(current_params['number'])

    current_params['credit'] = decimal_2_float(float(current_params['credit']))

    if current_params['action'] != 'create_red_envelope':
        json_dict['message'] = "参数错误"
        json_dict['error_ext'] = "action"
        return display_json(json_dict)
    if len(current_params['group_id']) < 5 and len(current_params['user_id']) < 3:
        json_dict['message'] = "参数错误"
        json_dict['error_ext'] = "group_id|user_id特殊可选"
        return display_json(json_dict)

    if current_params['number'] < 1 or current_params['number'] > pay_config['red_envelope']['max_number']:
        json_dict['message'] = "红包数量不合法"
        json_dict['error_ext'] = "number"
        return display_json(json_dict)

    if current_params['rtype'] == 'normal':
        current_params['credit'] = decimal_2_float(current_params['number'] * current_params['credit'])
    else:
        current_params['rtype'] == 'lucky'

    if current_params['credit'] < 0.01:
        json_dict['message'] = "红包金额不能小于0.01元"
        json_dict['error_ext'] = "credit"
        return display_json(current_params)

    if current_params['credit'] > pay_config['red_envelope']['max_credit']:
        json_dict['message'] = "单个红包金额不可超过%s元" % (pay_config['red_envelope']['max_credit'])
        json_dict['error_ext'] = "credit"
        json_dict['error_code'] = 4010
        return display_json(json_dict)

    if decimal_2_float(current_params['credit'] / current_params['number']) < 0.01:
        json_dict['message'] = "单个红包金额不可小于0.01元"
        json_dict['error_ext'] = "credit"
        return display_json(json_dict)

    if decimal_2_float(current_params['credit'] / current_params['number']) < 0.01:
        json_dict['message'] = "单个红包金额不可小于0.01元"
        json_dict['error_ext'] = "credit"
        return display_json(json_dict)

    if decimal_2_float(current_params['credit'] / current_params['number']) > pay_config['red_envelope']['single_max_credit']:
        json_dict['message'] = "单个红包金额最大%s 元" % pay_config['red_envelope']['single_max_credit']
        json_dict['error_ext'] = "credit"
        return display_json(json_dict)

    if len(str(current_params['content'])) == 0:
        current_params['content'] = "恭喜发财，大吉大利！"

    if len(str(current_params['content'])) > 30:
        current_params['content'] = str(current_params['content'])[0:30]

    current_params['group_chat_id'] = []
    if len(current_params['group_id']) > 0:
        current_params['group_chat_id'].append(current_params['group_id'])
    if len(current_params['user_id']) > 0:
        current_params['group_chat_id'].append(current_params['user_id'])


    try:
        # 如果是支付宝的取支付宝帐户
        if pay_config['pay_channel'] == "alipay":
            user_pay_info = rels.get_user_pay_alipay_account(user_id)
            pay_account = user_pay_info['alipay_login_account']
            if len(pay_account) == 0:
                json_dict['message'] = "用户没有绑定支付宝帐户"
                json_dict['error_ext'] = "alipay_login_account"
                return display_json(json_dict)
        else:
            # 其他支付方式 在取
            user_pay_info = {""}
            pay_account = ""
            pass

        # 创建订单
        format_order_params = {
            "order_type": "red_envelope",
            "pay_channel": pay_config['pay_channel'],
            "pay_account": pay_account,
            "credit": current_params['credit'],
            "remain_credit": current_params['credit'],
            "create_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "order_comments": {}
        }
        po = PayOrder(**format_order_params)
        today_pay = po.get_user_today_pay_red_envelope()

        if (today_pay + current_params['credit']) > pay_config['red_envelope']['day_pay_credit_limit']:
            json_dict['message'] = "已达到单日支付限额"
            json_dict['error_ext'] = "credit"
            return display_json(json_dict)

        order_result = po.create()
        if order_result['ret'] != 1:
            json_dict['error_code'] = order_result['error_code']
            json_dict['message'] = "创建红包失败"
            return display_json(order_result)

        # 创建红包
        order_id = order_result["data"]['id']
        order_no = po.get_order_no()
        format_params = {
            "host_id": rels.host_id,
            "user_id": user_id,
            "order_id": order_id,
            "number": current_params['number'],
            "credit": current_params['credit'],
            "balance": current_params['credit'],
            "red_type": current_params['rtype'],
            "red_number": current_params['number'],
            "draw_number": 0,
            "red_content": current_params['content'],
            "group_chat_id": current_params['group_chat_id'],
            "create_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "expire_time": time.strftime("%Y-%m-%d %H:%M:%S",
                                         time.localtime(time.time() + pay_config['red_envelope']['expiry_time'])),
        }

        rel = RedEnvelope(**format_params)
        red_result = rel.create()

        if red_result['ret'] != 1:
            json_dict['error_code'] = red_result['error_code']
            json_dict['message'] = "创建红包失败"
            return display_json(json_dict)

        red_id = red_result["data"]['id']

        # 缓存红包信息
        rel.cache_red_info(red_id)
        # 有红包id了， 有订单id ,生成订单流水

        trace_result = po.insert_order_trace()

        if trace_result['ret'] != 1:
            json_dict['error_code'] = trace_result['error_code']
            json_dict['message'] = "创建红包失败"
            return display_json(json_dict)
        order_line = trace_result['data']['order_line']
        # 订单流水用于 生成支付链接参数

        # 创建红包成功后 生成支付信息， 订单流水
        if pay_config['pay_channel'] == "alipay":
            pa = PayAlipay()
            pay_params = pa.get_app_pay(order_no=order_no, amount=current_params['credit'],
                                        alipay_uid=pay_account,
                                        title=pay_config['red_envelope']['bill_title'])

            json_dict['ret'] = 1
            json_dict['error_code'] = 200
            json_dict['message'] = "初始化红包成功"
            json_dict['data']['pay_channel'] = pay_config['pay_channel']
            json_dict['data']['pay_parmas'] = pay_params
            json_dict['data']['rid'] = red_id
            return display_json(json_dict)
        else:
            # 其他支付方式 在取
            json_dict['error_code'] = 4023
            json_dict['message'] = "不支持的支付方式"
            return display_json(json_dict)

    except Exception as e:
        json_dict['error_code'] = e
        if not is_int(json_dict['error_code']):
            rels.write_error_log("red_envelope", "红包id:%s出错%s" % (0, json_dict['error_code']))
            json_dict['error_code'] = 0

        json_dict['message'] = "创建红包失败!"
        json_dict['error_ext'] = ""
        return display_json(json_dict)
