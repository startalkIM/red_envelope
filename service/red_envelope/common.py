#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'suozhu.li'

from flask import Blueprint, Response, json, request, jsonify
import requests
from conf.constants import *
from utils.authorization import check_ckey
from utils.request_util import RequestUtil
from utils.logger_conf import configure_logger
from utils.common_sql import domains
log_path = get_logger_file('read_envelope_check_ck.log')
ck_logger = configure_logger('read_envelope_check_ck', log_path)

"""
认证用户ckey 并返回ckey中的用户id 
"""
r_domain = domains if domains else []


def authorization(func):
    def wrapper(*args, **kw):
        # ckey = ''
        # user_id = ''
        request_util = RequestUtil()
        user_id = request_util.get_user(request)
        res = False
        if is_check_ckey:
            ckey = request_util.get_ckey(request)
            if ckey:
                if auth_ckey_url:
                    try:
                        r_data = {
                            'ckey': ckey,
                            'system': 'red_envelope'
                        }
                        ret = requests.post(url=auth_ckey_url, json=r_data)
                        # r_domain.append(ret.json().get('data').get('d'))
                        ck_logger.info("ckey:{},ret:{}".format(ckey, ret.text))
                        if ret.json().get('ret'):
                            # if ret.json().get('data').get('d') != r_domain:
                            #    return jsonify(ret=0, message="Error domain")
                            res = True
                            user_id = ret.json().get('data').get('u')
                    except (requests.RequestException or KeyError) as e:
                        ck_logger.error("ckey api failed : {}".format(e))
                        # TODO notify developer to check
                        # res = check_ckey(ckey, user_id)
                        res, user_id = check_ckey(ckey)

                    except Exception as e:
                        ck_logger.error("ckey api failed : {}".format(e))
                else:
                    res, user_id = check_ckey(ckey)
            if res:
                return func(user_id=user_id, *args, **kw)
            else:
                ck_logger.info("user:{user} login failed, ckey : {ckey}, \
                                                ".format(user=user_id, ckey=ckey))
                return jsonify(ret=0, message="ckey check failed")
        return func(user_id=user_id, *args, **kw)

    wrapper.__name__ = func.__name__
    return wrapper


"""
返回 flask 展示json
"""


def display_json(dict_arr):
    return Response(json.dumps(dict_arr, ensure_ascii=False), mimetype='application/json')


"""
获取 需要的url 提交参数
"""


def get_request_need_args(**current_params):
    current_args = RequestUtil.get_request_args(request)
    has_var = current_params.keys() & current_args.keys()
    for pk in has_var:
        current_params[pk] = current_args[pk]
    return current_params


"""
 校验手机号
"""


def validate_mobile(value):
    if re.search('^1[0-9]{10}$', str(value)):
        return True
    return False


"""
校验邮箱
"""


def validate_email(value):
    if re.match(r'^([\w]+\.*)([\w]+)\@[\w]+\.\w{3}(\.\w{2}|)$', str(value)):
        return True
    return False


"""

转换 数字字符串 成浮点型 ， 默认保留两位小数
注: 不四舍不入
不用 round(x,2)
不用 decimal
"""


def decimal_2_float(number, prec=2):
    if type(number) is not float and type(number) is not int:
        number = float(number)
    # 使用格式化 浮点数 多一位，防止四舍五入， 返回截取最后一位前所有的，再转换为符点型
    prec = prec + 1
    return float((('%.' + str(prec) + 'f') % number)[:-1])


"""
是否是整型数字
注不要使用 isnumeric|isdigit 这个阿拉伯数字 汉字 罗马数字均返回True
isdecimal
"" 空串 none 
"""


def is_int(number):
    try:
        if number is None or len(str(number)) == 0:
            return False
        result = re.match(r'^\d+$', str(number))
        if result:
            return True
        else:
            result = re.match(r'\d+\.0*$', str(number))
            if result:
                return True
            return False
    except Exception as e:
        return False


"""
判断 字符串是否是字符串

"" 空串 none 
"""


def is_float(number):
    try:
        if number is None or len(str(number)) == 0:
            return False
        result = re.match(r'^\d*\.\d*|\d*$', str(number))
        if result:
            return True
        else:
            return False
    except Exception as e:
        return False


"""
分析 pgsql execute 后的执行状态 
插入 返回 'INSERT 0 3'
删除 返回 'DELETE 1'
更新 返回  UPDATE 3
更新 返回  SELECT 9
以下均返回1个 无影响行数
BEGIN 
COMMIT
ROLLBACK
"""


def parse_psycopg2_statusmessage(statusmessage):
    if type(statusmessage) is not str:
        statusmessage = str(statusmessage)
    result = statusmessage.split(" ")
    # insert 返回的是 三个参数 ，其他返回两个参数
    if result[0] == 'INSERT':
        return int(result[2])
    elif result[0] in ['DELETE', 'UPDATE', 'SELECT']:
        return int(result[1])
    elif result[0] in ['BEGIN', 'COMMIT']:
        return str(result[0])
    else:
        return statusmessage
