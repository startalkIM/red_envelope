#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
定时脚本，发送发红包消息， 以及已抢红包消息
"""
import os
import sys

# 增加system path 以便获取对应的自定义包
sys.path.append(os.path.abspath(os.path.dirname(__file__)+"/../../"))
from service.red_envelope.common import *
from service.red_envelope.RedEnvelopeQtalkMessage import RedEnvelopeQtalkMessage
from service.red_envelope.crontab_common import RedEnvCrontab

r_log = configure_logger("red_envelope_qtalkmessage")

# 判断程序是否正在运行，没有运行打上pid标记
is_run = RedEnvCrontab.crontab_run_begin(__file__)

if is_run:
    r_log.info("is_run")
    sys.exit("程序正在执行")

r_log.info("begin")

re = RedEnvelopeQtalkMessage()
redis_cli = re.redis_cli

# 消息队列的 redis key
rkey = re.get_qtalk_message_queue_redis_key()

# 没有数据的自增值
not_result_number = 0

# brpop 超时时间是30秒
bpop_timeout = 30
# 程序多长时间没有消息就退出，访止程序修改不更新
max_timeout = 300

while True:
    print(".")
    if bpop_timeout*not_result_number >= max_timeout:
        # 当没有队列超过多少秒退出循环
        r_log.info("无队列超时%d秒,退出" % max_timeout)
        break
    try:
        info = redis_cli.blpop(rkey, bpop_timeout)
    except Exception as e:
        info = None
        r_log.info("获取redis blpop失败:%s" % str(e))

    if not info:
        not_result_number = not_result_number + 1
        continue

    not_result_number = 0
    msg_info = json.loads(info[1])

    # 拆红包消息
    if msg_info['msg_type'] == "open_success":
        send_result = re.send_red_env_open_message(msg_info=msg_info, r_log=r_log)
        r_log.info("open_success：发送消息%s;原消息体：%s" % ("成功" if send_result else "失败", msg_info))
    elif msg_info['msg_type'] == "pay_success":
        # 发红包支付成功消息
        send_result = re.send_red_env_create_message(msg_info=msg_info, r_log=r_log)
        r_log.info("open_success：发送消息%s;原消息体：%s" % ("成功" if send_result else "失败", msg_info))


RedEnvCrontab.crontab_run_done(__file__)
r_log.info("done")
