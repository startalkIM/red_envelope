#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'jingyu.he'
import redis
from redis import sentinel
from conf.cache_params_define import *
# from utils.logger_conf import configure_logger

# log_path = get_logger_file(name='reids.log')
# redis_log = configure_logger('redis', log_path)

try:
    if if_redis_sentinel:
        _hosts = [hp.split(':') for hp in pre_rs_hosts]
        hosts = [(hp[0].strip(), int(hp[1].strip())) for hp in _hosts]
        r_sentinel = sentinel.Sentinel(hosts, socket_timeout=r_timeout)
        redis_cli = r_sentinel.master_for(r_master, socket_timeout=r_timeout, password=r_password, db=r_database,
                                          decode_responses=True)
    else:
        redis_cli = redis.StrictRedis(host=r_host, port=r_port, db=r_database, password=r_password,
                                      decode_responses=True)
except (KeyError, ValueError, IndexError) as e:
    raise TypeError('wrong configure pattern')
    # redis_log.exception('wrong configure pattern')
    # exit(0)


class RedisUtil:
    def __init__(self):
        self.redis = redis_cli
        self.single_key = SINGLE_KEY
        self.muc_key = MUC_KEY
        self.single_trace_key = SINGLE_TRACE_KEY
        self.muc_trace_key = MUC_TRACE_KEY
        # self.router = [self.single_key, self.muc_key, self.single_trace_key, self.muc_trace_key]

    def get_user_habit(self, user_id):
        """
        获取redis中用户的缓存
        包括个人、群组聊天顺序
        个人、群组聊天频率
        :param user_id:
        :return:
        """
        router = [self.single_key, self.muc_key, self.single_trace_key, self.muc_trace_key]
        habit = {}
        for key in router:
            _k = key + '_' + user_id
            if key in [self.single_key, self.muc_key]:
                habit[key] = self.redis.lrange(name=_k, start=0, end=-1)
            else:
                habit[key] = self.redis.zrevrangebyscore(name=_k, max='+inf', min=10, start=0, num=10)
                # TODO 这个num可能应该走limit 和 offset
        return habit

