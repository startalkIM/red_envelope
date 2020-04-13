#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
支付宝第三方登录oauth回调
此页面暂时仅 沙盒开发测试 拿uid使用
"""
from service.red_envelope.common import *
from service.red_envelope.PayAlipay import PayAlipay

alipay_oauth_blueprint = Blueprint('alipay_oauth', __name__)


@alipay_oauth_blueprint.route('/oauth')
@authorization
def current(user_id=None):
    json_dict = {"ret": 0, "message": "", "error_code": 0, "error_ext": "",
                 "data": {"pay_channel": "", "pay_parmas": "", "rid": 0}}

    if user_id == 'DEFAULT' or user_id is None or len(str(user_id)) == 0:
        json_dict['message'] = "未登录用户"
        json_dict['user_id'] = user_id
        return display_json(json_dict)

    current_params = {
            # 公共参数
            "app_id": "", "source": "", "app_auth_code": ""
            }
    # 获取本页面必要参数
    current_params = get_request_need_args(**current_params)

    pa = PayAlipay()
    rs = pa.oauth(current_params['app_auth_code'])

    return display_json(rs)
