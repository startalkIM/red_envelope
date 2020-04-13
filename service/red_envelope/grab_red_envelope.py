#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
/red_envelope/grab
拆红包

"""
from service.red_envelope.common import *

from service.red_envelope.common_sql import RedEnvelopeSql
from service.red_envelope.RedEnvelope import RedEnvelope

grab_red_envelope_blueprint = Blueprint('grab_red_envelope', __name__)


@grab_red_envelope_blueprint.route('/grab')
@authorization
def current(user_id=None):
    json_dict = {"ret": 0, "message": "", "error_code": 0, "error_ext": "", "data": {}}

    if user_id == 'DEFAULT' or user_id is None or len(str(user_id)) == 0:
        json_dict['message'] = "未登录用户"
        json_dict['user_id'] = user_id
        return display_json(json_dict)

    # 本页面 必要参数
    """
    公共参数
    action 必须是 grab_red_envelope
    group_id 红包所在群id e68c88425a4745b5af9e7a9e7465df08@conference.ejabhost1 特殊可选 group_id 与user_id 必选其1
    user_id 收红包的人 suozhu.li@ejabhost1

    rid 红包id
    """

    current_params = {
        # 公共参数
        "action": None, "group_id": "", "user_id": "",
        # 必要参数
        "rid": 0
    }
    # 获取本页面必要参数
    current_params = get_request_need_args(**current_params)

    if current_params['action'] != 'grab_red_envelope':
        json_dict['message'] = "参数错误"
        json_dict['error_ext'] = "action"
        return display_json(json_dict)
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

    user_info = rels.get_user_pay_alipay_account(user_id=user_id)
    if user_info['id'] is None:
        # 红包不存在　
        json_dict['error_code'] = 4300
        json_dict['error_ext'] = "user"
        json_dict['message'] = "用户未绑定支付宝"
        return display_json(json_dict)

    try:
        rel = RedEnvelope()
        red_info = rel.get_red_info_from_cacheordb(current_params['rid'])

        if red_info is None:
            # 红包不存在　
            json_dict['error_code'] = 4002
            json_dict['message'] = rel.error_code['4002']
            return display_json(json_dict)
        """
            是否有权拆红包 has_power
            是否已过期 is_expired
            是否抢光 is_out
            自已是否抢过 is_grab

            是否能拆 
        """
        if not rel.check_power(group_id=group_id, group_chat_id=red_info['group_chat_id']):
            # 无权抢红包　
            json_dict['error_code'] = 4022
            json_dict['message'] = rel.error_code['4022']
            return display_json(json_dict)

        if rel.check_expired(red_info['expire_time']):
            # 红包已过期　
            json_dict['error_code'] = 4005
            json_dict['message'] = rel.error_code['4005']
            return display_json(json_dict)

        if rel.check_is_out(red_id=current_params['rid']):
            # 红包已抢光　
            json_dict['error_code'] = 4007
            json_dict['message'] = rel.error_code['4007']
            return display_json(json_dict)

        grab_count = rel.get_day_grab_count(host_id=red_info['host_id'], send_user_id=red_info['user_id'],
                                            grab_user_id=current_params['user_id'])
        if grab_count >= pay_config['red_envelope']['grab_c2c_day_max_number']:
            # 抢同一红包用户红包超限　
            json_dict['error_code'] = 4030
            json_dict['message'] = rel.error_code['4007']
            return display_json(json_dict)

        # 执行拆红包的动作
        result = rel.grab(host_id=rels.host_id, user_id=user_id, red_id=current_params['rid'], group_id=group_id)
        if 'sql_error' in result.keys():
            del result['sql_error']
        return display_json(result)

    except Exception as e:
        json_dict['error_code'] = str(e)

        if not is_int(json_dict['error_code']):
            rels.write_error_log("red_envelope", "红包id:%s出错%s" % (current_params['rid'], json_dict['error_code']))
            json_dict['error_code'] = 0

        json_dict['message'] = "获取红包信息失败"
        json_dict['error_ext'] = ""
        return display_json(json_dict)



