#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
/red_envelope/get
获取红包信息，以及红包拆的列表
"""
import time
from service.red_envelope.common import *

from service.red_envelope.common_sql import RedEnvelopeSql
from service.red_envelope.RedEnvelope import RedEnvelope
from service.red_envelope.PayOrder import PayOrder


get_red_envelope_blueprint = Blueprint('get_red_envelope', __name__)


@get_red_envelope_blueprint.route('/get')
@authorization
def current(user_id=None):
    json_dict = {"ret": 0, "message": "", "error_code": 0, "error_ext": "",  "data": {}}
    # 本页面 必要参数
    """
    公共参数
    group_id 红包所在群id e68c88425a4745b5af9e7a9e7465df08@conference.ejabhost1 特殊可选 group_id 与user_id 必选其1
    user_id 收红包的人 suozhu.li@ejabhost1

    rid 红包id
    """

    current_params = {
        # 公共参数
        "group_id": "", "user_id": "",
        # 必要参数
        "rid": 0
    }
    # 获取本页面必要参数
    current_params = get_request_need_args(**current_params)
    if len(current_params['group_id']) < 5 and len(current_params['user_id']) < 3:
        json_dict['message'] = "参数错误"
        json_dict['error_ext'] = "group_id|user_id特殊可选"
        return display_json(json_dict)

    # 验权用
    group_id = current_params['group_id'] if len(current_params['group_id']) > 0 else current_params['user_id']
    if not is_int(current_params['rid']):
        # 红包不存在　
        json_dict['error_code'] = 4002
        json_dict['error_ext'] = "id"
        json_dict['message'] = "参数错误"
        return display_json(json_dict)

    current_params['rid'] = int(current_params['rid'])
    rels = RedEnvelopeSql()


    try:
        rel = RedEnvelope()
        red_info_res = rel.get_info(red_id=current_params['rid'])
        red_info = red_info_res['data']
        if not red_info_res['ret'] or not red_info:
            # 红包不存在　
            json_dict['error_code'] = 4002
            json_dict['message'] = rel.error_code['4002']
            return display_json(json_dict)
        """
            是否有权限看
            不是自已发的， 或群组不在红包组里边
        """

        po = PayOrder(id=red_info['order_id'])

        if po.get_state() == 'unpay':
            # 红包如果没支付不返回红包信息
            json_dict['error_code'] = 4002
            json_dict['message'] = rel.error_code['4002']
            return display_json(json_dict)
        red_info['draw_record'] = rel.get_draw_record_list(red_id=current_params['rid'])

        is_grab = False
        last_draw_time = None
        for k in red_info['draw_record']:
            last_draw_time = k['last_draw_time']
            if k['user_id'] == user_id:
                is_grab = True

        if not is_grab and not (rels.host_id == red_info['host_id'] and user_id == red_info['user_id']) and not rel.check_power(group_id=group_id, group_chat_id=red_info['group_chat_id']):
            # 无权红包　
            json_dict['error_code'] = 4022
            json_dict['message'] = rel.error_code['4022']
            return display_json(json_dict)


        # 不能返回红包的群id，防止窃取 支付信息
        del red_info['group_chat_id']
        del red_info['id']
        del red_info['order_id']
        # 是否显示红包最佳
        red_info['show_rank'] = 1 if red_info['is_expire'] == 1 or red_info['is_grab_over'] == 1 else 0

        red_info['grab_over_time'] = 0

        if last_draw_time is not None and red_info['is_grab_over'] == 1:
            grab_over_time = int(time.mktime(time.strptime(last_draw_time, "%Y-%m-%d %H:%M:%S")))-int(time.mktime(time.strptime(red_info['create_time'], "%Y-%m-%d %H:%M:%S")))
            if grab_over_time < 100:
                red_info['grab_over_time'] = grab_over_time

        json_dict['ret'] = 1
        json_dict['data'] = red_info
        json_dict['message'] = "获取成功"
        json_dict['error_ext'] = ""

        return display_json(json_dict)

    except Exception as e:
        json_dict['error_code'] = str(e)

        if not is_int(json_dict['error_code']):
            rels.write_error_log("red_envelope", "查看红包信息：红包id:%s出错%s" % (current_params['rid'], json_dict['error_code']))
            json_dict['error_code'] = 0

        json_dict['message'] = "获取红包信息失败"
        json_dict['error_ext'] = ""
        return display_json(json_dict)
