#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'jingyu.he'
import psycopg2
import re
from utils.get_conf import get_config_file, get_logger_file
from utils.logger_conf import configure_logger
from conf.constants import PY_VERSION as PYTHON_VERSION, DB_VERSION as DATABASE_VERSION
from utils.redis_utils import redis_cli

config = get_config_file()
pgconfig = config['postgresql']
host = pgconfig['host']
port = pgconfig['port']
user = pgconfig['user']
database = pgconfig['database']
password = pgconfig['password']
if_cached = config['cache'].getboolean('if_cache')

log_path = get_logger_file('sql.log')
sql_logger = configure_logger('sql', log_path)
if_async = None
PY_VERSION = PYTHON_VERSION
DB_VERSION = DATABASE_VERSION

user_data = {}
domains = None


class UserLib:
    def __init__(self):
        self.conn = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
        self.conn.autocommit = True

    def close(self):
        if self.conn:
            self.conn.close()

    def get_db_version(self):
        _version = False
        conn = self.conn
        sql = "SELECT version();"
        cursor = conn.cursor()
        cursor.execute(sql)
        rs = cursor.fetchall()
        for row in rs:
            row = ['' if x is None else x for x in row]
            _version = row[0]
        _result = re.findall('postgresql\s(\d.*?)\son', _version.lower())
        if _result and len(_result) != 0:
            _version = _result[0]
        else:
            _version = False
        cursor.close()
        return _version

    def get_domains(self):
        conn = self.conn
        sql = """select host from host_info """
        cursor = conn.cursor()
        cursor.execute(sql)
        rs = cursor.fetchall()
        domains = []
        for domain in rs:
            domains.append(domain[0])
        cursor.close()
        return domains


if DB_VERSION is None:
    __user_lib = UserLib()
    DB_VERSION = __user_lib.get_db_version()
    __user_lib.conn.close()
    sql_logger.info('PGSQL VERSION : {}'.format(DB_VERSION))

if domains is None:
    __user_lib = UserLib()
    domains = __user_lib.get_domains()
    __user_lib.conn.close()
    sql_logger.info('Domains : {}'.format(domains))

# if if_async is None:
#     __user_lib = AsyncLib()
sql_logger.info('USE ASYNC : {}'.format(if_async == True))
