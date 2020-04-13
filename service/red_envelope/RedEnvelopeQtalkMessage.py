#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
红包相关消息，发红包消息， 收红包消息
"""

from flask import json
from utils.send_qtalk_message_utils import QtalkMessage
from service.red_envelope.RedEnvelope import RedEnvelope


class RedEnvelopeQtalkMessage(RedEnvelope):
    def __init__(self, ):
        super().__init__()

    """
    判断 是否是群消息
    """
    def is_group_chat(self, group_id):
        return True if group_id.find("conference") > 0 else False
    """
    发送创建红包的消息
    
    {"id": "5", "msg_type": "pay_success" ."group_id": group_id}
    """
    def send_red_env_create_message(self, msg_info, r_log=None):
        if not isinstance(msg_info, dict):
            return False

        if "id" not in msg_info.keys():
            return False

        red_info_res = self.get_info(red_id=msg_info['id'])
        if not red_info_res['ret'] or not red_info_res['data']:
            return False

        red_info = red_info_res['data']

        if "group_id" in msg_info.keys():
            group_id = msg_info['group_id']
        else:
            group_id = red_info['group_chat_id'][0]

        group_id_info = group_id.split("@")

        is_group = self.is_group_chat(group_id)
        to_user = group_id_info[0]
        try:
            to_host = group_id_info[1]
        except Exception as e:
            # 如果验证失败，返回假值。
            to_host = ''

        body = "[红包] 仅支持高版本app，请在手机版本app中打开查看"

        red_type_str = "红包"
        if red_info['red_type'] == "lucky":
            red_type_str = "拼手气红包"
        elif red_info['red_type'] == "normal":
            red_type_str = "普通红包"

        params = {
            "from": red_info['user_id'],
            "fromhost": red_info['host'],
            "to": [{"user": to_user, "host": to_host}],
            "content": body,
            "type": "groupchat" if is_group else "chat",
            "extendinfo": {
                "url": red_info['id'],  # 打开红包的url
                "rid": red_info['id'],  # 红包id
                "type": red_type_str,  # 红包类型， normal=普通红包,lucky=拼手气
                "typestr": red_info['red_content'],  # 红包类型字符串表示
                "content": red_info['red_content'],  # 红包内容
            }
        }
        if r_log:
            r_log.info(json.dumps(params, ensure_ascii=False))

        return QtalkMessage.send(512, **params)

    """
    发送创建红包的消息
    
    小红包， 抢红包时所在的group
    params = {"msg_type": "open_success", "id": srid, "group_id": group_id}
    
    如果需要记录日志 r_log 传 configure_logger("red_envelope_qtalkmessage")
    """

    def send_red_env_open_message(self, msg_info, r_log=None):

        if not isinstance(msg_info, dict):
            return False

        if "id" not in msg_info.keys() or "group_id" not in msg_info.keys():
            return False

        draw_record = self.get_draw_record_info(srid=int(msg_info['id']))
        if not draw_record:
            return False
        red_info_res = self.get_info(red_id=draw_record['red_envelope_id'])
        if not red_info_res['ret'] or not red_info_res['data']:
            return False

        red_info = red_info_res['data']

        group_id_info = msg_info['group_id'].split("@")

        is_group = self.is_group_chat(msg_info['group_id'])
        to_user = group_id_info[0]
        try:
            to_host = group_id_info[1]
        except Exception as e:
            # 如果验证失败，返回假值。
            to_host = ''

        # 红包剩余数量 redis 存放，访止消息对不上
        red_remain_number_key = self.get_redis_key(red_id=draw_record['red_envelope_id'], column="remain_number")
        self.redis_cli.decr(red_remain_number_key)
        remain_num = int(self.redis_cli.get(red_remain_number_key))

        body = "[红包] %s领取了%s的红包" % (draw_record['user_name'], red_info['user_name'])

        if remain_num > 0:
            body = body+",剩余%d个" % remain_num
        else:
            body = body + ",红包已被领完"

        red_type_str = "红包"
        if red_info['red_type'] == "lucky":
            red_type_str = "拼手气红包"
        elif red_info['red_type'] == "normal":
            red_type_str = "拼手气红包"

        params = {
            "from": draw_record['user_id'],
            "fromhost": draw_record['host'],
            "to": [{"user": to_user, "host": to_host}],
            "content": body,
            "type": "groupchat" if is_group else "chat",
            "extendinfo": {
                "Url": red_info['id'],  # 打开红包的url
                "Rid": red_info['id'],  # 红包id
                "From_User": "%s@%s" % (red_info['user_id'], red_info['host']),  # 发红包的人
                "From_User": "%s@%s" % (red_info['user_id'], red_info['host']),  # 打开红包的人
                "Type": red_info['red_type'],  # 红包类型， normal=普通红包,lucky=拼手气
                "Typestr": red_type_str,  # 红包类型字符串表示
                "Balance": remain_num,  # 红包剩余量
             }
        }
        if r_log:
            r_log.info(json.dumps(params, ensure_ascii=False))

        return QtalkMessage.send(15, **params)


