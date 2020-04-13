#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'jingyu.he'
import base64
import hashlib
import redis
from redis import sentinel
from urllib.parse import parse_qs
from conf.constants import *
from utils.logger_conf import configure_logger
from utils.get_conf import *
from service.red_envelope.common import *


log_path = get_logger_file()
log_path = log_path + 'author.log'
author_log = configure_logger('author', log_path)

try:
    redis_cli = redis.StrictRedis(host=r_host, port=r_port, db=r_database, password=r_password,
                                  decode_responses=True)
except (KeyError, ValueError, IndexError) as e:
    author_log.exception('wrong configure pattern')
    exit(0)

author_log.info("REIDS START SUCCESS")
g_user = ''


def check_ckey(ckey, puser=''):
    global g_user
    user_id = ''
    if not isinstance(ckey, str):
        ckey = str(ckey)
    if len(ckey) <= 0:
        return False
    try:
        ckey_parse = base64.b64decode(ckey).decode('utf-8')
        result = parse_qs(ckey_parse)
        # user = result['u'][0]
        user = result.get('u')
        if isinstance(user, list):
            user = user[0]
        if puser:
            if user != puser:
                return False, user
        # domain = result['d'][0]
        domain = result.get('d')
        if isinstance(domain, list):
            domain = domain[0]
        if not g_user:
            g_user = user
        # time = result['t'][0]
        _time = result.get('t')
        if isinstance(_time, list):
            _time = _time[0]
        tar = result['k']
        if isinstance(tar, list):
            tar = tar[0]
        if domain == r_domain:
            user_keys = redis_cli.hkeys(user)
            if isinstance(user_keys, list):
                for i in user_keys:
                    i = str(i) + str(_time)
                    i = md5(i)
                    i = str(i).upper()
                    if i == str(tar):
                        if g_user != user:
                            g_user = user
                            author_log.info('user = {} , ckey = {} login success!'.format(result['u'][0], ckey))
                        return True, user
            elif isinstance(user_keys, (str, int)):
                i = str(user_keys) + str(_time)
                i = md5(i)
                i = str(i).upper()
                if i == str(tar):
                    if g_user != user:
                        g_user = user
                        author_log.info('user = {} , ckey = {} login success!'.format(result['u'][0], ckey))
                user_id = user + domain
                return True, user_id
            else:
                return False, user
            return False, user
        else:
            author_log.error("unknown domain {} get for user {}".format(result['d'][0], user))
            return False, user
    except Exception as e:
        author_log.exception("CKEY CHECK FAILED")
        return False, ''


def md5(string):
    m = hashlib.md5()
    m.update(string.encode("utf8"))
    return m.hexdigest()


def md5GBK(string1):
    m = hashlib.md5(string1.encode(encoding='gb2312'))
    return m.hexdigest()
