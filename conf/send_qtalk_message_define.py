#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
用于qtalk 发消息用
用于utils/send_qtalk_message_utils.py
"""
from utils.get_conf import get_config_file
config = get_config_file()

qtalk_send_message_url = config['qtalk_send_message']['send_url']
qtalk_send_message_system = config['qtalk_send_message']['system']
