#!/usr/bin/env python
# -*- coding:utf-8 -*-

from utils.request_util import RequestUtil
from flask import request, jsonify
from conf.constants import *
from utils.authorization import check_ckey
from utils.logger_conf import configure_logger
import requests

log_path = get_logger_file('read_envelope_check_ck.log')
ck_logger = configure_logger('read_envelope_check_ck', log_path)


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
                            user_id = ret.json().get('data').get('u') + '@' + ret.json().get('data').get('d')
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
