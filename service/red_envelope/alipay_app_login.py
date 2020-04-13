#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
/red_envelope/alipay_app_login
"""

from service.red_envelope.common import *
from service.red_envelope.PayAlipay import PayAlipay


alipay_app_login_blueprint = Blueprint('alipay_app_login', __name__)


@alipay_app_login_blueprint.route('/alipay_app_login', methods=['POST', 'GET'])
@authorization
def current(user_id=None):
    json_dict = {"ret": 0, "message": "", "error_code": 0, "error_ext": "",
                 "data": ""}

    pa = PayAlipay()

    json_dict['ret'] = 1
    json_dict['error_code'] = 200
    json_dict['message'] = "成功"
    json_dict['data'] = pa.get_app_auth()
    return display_json(json_dict)
