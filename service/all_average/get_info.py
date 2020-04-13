#!/usr/bin/env python
# -*- coding:utf-8 -*-
import time
from flask import Blueprint, jsonify
from service.red_envelope.common import *
from service.red_envelope.PayAlipay import PayAlipay
from service.red_envelope.common import authorization, get_request_need_args, pay_config
from service.red_envelope.PayOrder import PayOrder
from service.all_average.common_sql import AllAverageSql

get_all_average_blueprint = Blueprint('get_all_average', __name__)


@get_all_average_blueprint.route('/getaa', methods=['POST'])
@authorization
def getaa(user_id: str = None):
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
        "aid": None
    }
    current_params = get_request_need_args(**current_params)
    aid = current_params['aid']

    """
    获取用户是否在aa所在成员
    """
    aas = AllAverageSql()
    is_qualified = aas.check_user_identify(aid=aid, user_id=user_id)
    if not is_qualified:
        json_dict['message'] = "用户无权查看aa"
        json_dict['user_id'] = user_id
        return jsonify(json_dict)

    status = {
        "type":"", # normal / custom
        "content": "",
        "aa_status": 0,  # 0：未收齐， 1：已收齐， 2：已过期
        "summary": 0.00,
        "incoming": 0.00,
        "organizer":"",
        "detail": {}
    }
    aa_status = aas.get_aa_status(aid=aid)
    ret = {**status, **aa_status}
