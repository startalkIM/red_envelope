#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import re
from utils.get_conf import get_logger_file, get_config_file

config = get_config_file()
logger_path = get_logger_file()

"""
ckey验证使用
"""
if_redis_sentinel = config['redis'].getboolean('if_sentinel')
auth_ckey_url = config['qtalk']['auth_ckey_url']
is_check_ckey = config['qtalk'].getboolean('ckey_check')

r_host = config['redis']['host']
r_database = config['redis']['database']
r_timeout = config['redis']['timeout']
r_port = config['redis']['port']
r_password = config['redis']['password']

# 支付相关的配置 红包相关的
pay_config = {
    "pay_channel": config['pay']['pay_channel'],
    "alert_user_id": config['pay']['alert_user_id'].split(","),
    # 红包相关的
    "red_envelope": {
        "max_number": int(config['pay'].getint('red_envelope_max_number')),
        "max_credit": float(config['pay'].getint('red_envelope_max_credit')),
        "single_max_credit": float(config['pay'].getint('red_envelope_single_max_credit')),
        "day_pay_credit_limit": float(config['pay'].getint('red_envelope_day_pay_credit_limit')),
        "grab_c2c_day_max_number": float(config['pay'].getint('red_envelope_grab_c2c_day_max_number')),
        "bill_title": config['pay']['red_envelope_bill_title'],
        "grab_bill_title": config['pay']['red_envelope_grab_bill_title'],
        "expiry_time": int(config['pay'].getint('red_envelope_expiry_time'))
    },
    "all_average": {
        "max_number": int(config['pay'].getint('all_average_max_number')),
        # "max_credit": float(config['pay'].getint('all_average_max_credit')),
        # "single_max_credit": float(config['pay'].getint('all_average_single_max_credit')),
        # "day_pay_credit_limit": float(config['pay'].getint('all_average_day_pay_credit_limit')),
        # "grab_c2c_day_max_number": float(config['pay'].getint('all_average_grab_c2c_day_max_number')),
        "bill_title": config['pay']['all_average_bill_title'],
        "grab_bill_title": config['pay']['all_average_grab_bill_title'],
        "expiry_time": int(config['pay'].getint('all_average_expiry_time'))
    }
}
# 支付宝相关的后端配置
if pay_config['pay_channel'] == 'alipay':
    pay_config['pid'] = config['alipay']['pid']
    pay_config['appId'] = config['alipay']['appId']
    pay_config['rsaPrivateKey'] = open(os.path.dirname(__file__) + "/" + config['alipay']['rsaPrivateKey']).read()
    pay_config['rsaPublickKey'] = open(os.path.dirname(__file__) + "/" + config['alipay']['rsaPublickKey']).read()
    pay_config['alipayrsaPublicKey'] = open(
        os.path.dirname(__file__) + "/" + config['alipay']['alipayrsaPublicKey']).read()
    pay_config['alipayCertPublicKey_RSA2'] = os.path.dirname(__file__) + "/" + config['alipay'][
        'alipayCertPublicKey_RSA2']
    pay_config['alipayRootCert'] = os.path.dirname(__file__) + "/" + config['alipay']['alipayRootCert']
    pay_config['appCertPublicKey'] = os.path.dirname(__file__) + "/" + config['alipay']['appCertPublicKey']

    pay_config['sandbox_debug'] = config['alipay'].getboolean('sandbox_debug')
    pay_config['alipay_callback_oauth'] = config['alipay']['alipay_callback_oauth']
    pay_config['alipay_callback_gateway'] = config['alipay']['alipay_callback_gateway']

RESPONSE_ERROR = 'ERROR'
RESPONSE_ROOM_FULL = 'FULL'
RESPONSE_UNKNOWN_ROOM = 'UNKNOWN_ROOM'
RESPONSE_UNKNOWN_CLIENT = 'UNKNOWN_CLIENT'
RESPONSE_DUPLICATE_CLIENT = 'DUPLICATE_CLIENT'
RESPONSE_SUCCESS = 'SUCCESS'
RESPONSE_INVALID_REQUEST = 'INVALID_REQUEST'

IS_DEV_SERVER = os.environ.get('APPLICATION_ID', '').startswith('dev')


def get_py_version():
    py_version = False
    py_version = re.findall('^([\d\.].*?)\s', sys.version)
    try:
        py_version = py_version[0]
    except Exception as e:
        print(e)
        py_version = False
    return py_version


PY_VERSION = get_py_version()
DB_VERSION = None
if_cached = config['cache'].getboolean('if_cache')
