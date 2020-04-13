#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'suozhu.li'

import requests
import json
from conf.send_qtalk_message_define import *


class QtalkMessage:
    def __init__(self):
        pass

    """
    msg_type 1 普通消息
    512 = 发红包
    2048 = 拆红包消息
    513= 发aa
    1025= 支付AA
    """
    @staticmethod
    def send(msg_type=1, **kwargs):

        if msg_type in [513, 1025]:
            tips = "[AA收款]"
        else:
            tips = "[红包]"
        if "extendinfo" not in kwargs.keys():
            kwargs['extendinfo'] = ""

        # groupchat|chat
        if 'type' not in kwargs.keys() or kwargs['type'] not in ["chat", "groupchat"]:
            kwargs['type'] = 'chat'

        post_data_dic = {
            "from": kwargs['from'],
            "fromhost": kwargs['fromhost'],
            "to": kwargs['to'],
            "type": kwargs['type'],
            "extendinfo": json.dumps(kwargs['extendinfo'], ensure_ascii=False),
            "msgtype": str(msg_type),
            "content": kwargs['content'] if "content" in kwargs.keys() else (tips + " 仅支持高版本app，请在手机版本app中打开查看"),
            "auto_reply": "false",
            "system": qtalk_send_message_system,
             }
        r = requests.post(qtalk_send_message_url, json=post_data_dic, headers={'Content-Type': 'application/json'})
        result = r.json()
        return True if result['ret'] else False


