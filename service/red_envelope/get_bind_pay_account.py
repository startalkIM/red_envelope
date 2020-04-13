#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
/red_envelope/get_bind_pay_account
用于qt 获取绑定的支付帐户
"""
from service.red_envelope.common import *

from service.red_envelope.common_sql import RedEnvelopeSql

get_bind_pay_account_blueprint = Blueprint('get_bind_pay_account', __name__)


@get_bind_pay_account_blueprint.route('/get_bind_pay_account')
@authorization
def current(user_id=None):

    json_dict = {"ret": 0, "message": "", "data": {"pay_channel": pay_config['pay_channel'], "user_info": {}, "user_id":user_id}}

    if user_id == 'DEFAULT' or user_id is None or len(str(user_id)) == 0:
        json_dict['message'] = "未登录用户"
        json_dict['user_id'] = user_id
        return display_json(json_dict)
    rels = RedEnvelopeSql()

    # 是支付宝支付的，返回支付宝绑定
    if pay_config['pay_channel'] == 'alipay':
        user_info = rels.get_user_pay_alipay_account(user_id=user_id)
        if user_info['id'] is None:
            json_dict['message'] = "该用户未绑定支付宝"
            return display_json(json_dict)
        else:
            del user_info['id']
    json_dict['ret'] = 1
    json_dict['data']['user_info'] = user_info
    return display_json(json_dict)
