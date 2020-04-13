#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
/red_envelope/bind_alipay_account
用于qt用户绑定支付宝， 需要判断 付款渠道是否是支付宝
绑定帐户可以是手机号、邮箱任选其一g 登录支付宝的帐户
帐户用于红包打款
"""

from service.red_envelope.common import *

from service.red_envelope.common_sql import RedEnvelopeSql

bind_alipay_account_blueprint = Blueprint('bind_alipay_account', __name__)


@bind_alipay_account_blueprint.route('/bind_alipay_account', methods=['POST', 'GET'])
@authorization
def current(user_id=None):

    json_dict = {"ret": 0, "message": "", "error_ext": "",  "data": {}}
    if user_id == 'DEFAULT' or user_id is None or len(str(user_id)) == 0:
        json_dict['message'] = "未登录用户"
        json_dict['user_id'] = user_id
        return display_json(json_dict)

    if pay_config['pay_channel'] != 'alipay':
        json_dict['message'] = "用户不能绑定支付宝"
        json_dict['data']['ext'] = pay_config['pay_channel']
        return display_json(json_dict)

    # 本页面 必要参数
    current_params = {"account": None}
    # 获取本页面必要参数
    current_params = get_request_need_args(**current_params)

    current_params['account'] = current_params['account'].strip()

    # 授权的用户id
    if len(current_params['account']) < 4:
        json_dict['message'] = "支付宝uid错误"
        return display_json(json_dict)

    rels = RedEnvelopeSql()
    # 如果可以，判断 帐户是否是已被使用

    if rels.get_alipay_account_is_bind(user_id=user_id, alipay_login_account=current_params['account']):
        json_dict['message'] = "该支付帐户已绑定其他用户"
        return display_json(json_dict)

    # 如果未被使用入库 返回结果
    res = rels.bind_pay_alipay_account(user_id=user_id, alipay_login_account=current_params['account'])
    if res is True:
        json_dict['ret'] = 1
        json_dict['message'] = "绑定成功"
    else:
        json_dict['message'] = "绑定失功"

    return display_json(json_dict)


