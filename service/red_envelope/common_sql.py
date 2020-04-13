#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
红包相关sql 继承common_sql.UserLib

# psycopg2.extras.register_json(oid=3802, array_oid=3807, globally=True)
# psycopg2.extras.register_default_jsonb()

"""

__author__ = 'suozhu.li'

import psycopg2.extras
from utils.common_sql import UserLib, sql_logger, redis_cli
from utils.logger_conf import configure_logger
from service.red_envelope.common import *

# http://initd.org/psycopg/docs/extras.html#connection-and-cursor-subclasses
psycopg2.extras.register_default_json(loads=lambda x: x)
psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)

"""
红包相关sql 继承common_sql.UserLib 
"""
domain = r_domain


class RedEnvelopeSql(UserLib):
    def __init__(self):
        super().__init__()

        self._red_envelope_logger = configure_logger("red_envelope")
        self._order_list_logger = configure_logger("order_list")

        self._host_id = None
        # 设置host id
        if domain and len(domain) == 1:
            self.set_host_id(domain[0])

    """
    注意写日志，一定要写红包id, 订单id
    """

    def write_info_log(self, log_type, message):
        if log_type == 'red_envelope':
            self._red_envelope_logger.info(message)
        elif log_type == 'order_list':
            self._order_list_logger.info(message)

    """
      注意写日志一定要写红包id, 订单id
    """

    def write_error_log(self, log_type, message):
        if log_type == 'red_envelope':
            self._red_envelope_logger.error(message)
        elif log_type == 'order_list':
            self._order_list_logger.error(message)

    """
    获取redis 链接
    """

    def get_redis_conn(self):
        return redis_cli

    """
        获取 pg 链接
    """

    def get_pg_conn(self):
        return self.conn

    """
        获取 pg 查询方式返回 字典方式
    """

    def get_pg_dict_cursor(self):

        return self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    """
    获取 pg
    """

    def get_pg_cursor(self):
        return self.conn.cursor()

    def test(self):
        return self._host_id

    """
    获取 host_id
    """

    @property
    def host_id(self):
        return self._host_id

    """
     设置 当前domain 对应的host id
    """

    def set_host_id(self, host):

        sql = "SELECT id as host_id FROM public.host_info WHERE host=%(host_id)s limit 1;"
        pg_cursor = self.get_pg_dict_cursor()
        pg_cursor.execute(sql, {'host_id': host})
        row = pg_cursor.fetchone()

        if 'host_id' in row.keys():
            self._host_id = int(row['host_id'])
        pg_cursor.close()

    """
    获取用户绑定的alipay 帐户信息
    """

    def get_user_pay_alipay_account(self, user_id):
        sql = """SELECT id,alipay_login_account,alipay_bind_time ,alipay_update_time FROM 
              public.host_users_pay_account WHERE host_id=%(host_id)s and user_id = %(user_id)s
              """
        self.write_info_log('red_envelope', "dddd111")
        pg_cursor = self.get_pg_dict_cursor()
        self.write_info_log('red_envelope', "dddd1222")
        pg_cursor.execute(sql, {'host_id': self._host_id, 'user_id': user_id})
        self.write_info_log('red_envelope', "dddd1333")
        row = pg_cursor.fetchone()
        self.write_info_log('red_envelope', "dddd14444")
        pg_cursor.close()
        self.write_info_log('red_envelope', "5555")
        bind_info = {'id': None, 'alipay_login_account': "", 'alipay_bind_time': "", 'alipay_update_time': ""}

        if row is not None:
            for k in bind_info:
                if k in ['alipay_bind_time', 'alipay_update_time']:
                    # timestamp 格式出来的是date time (Mon, 03 Jun 2019 11:02:24 GMT)需要转换一下格式用于显示
                    bind_info[k] = row[k].strftime("%Y-%m-%d %H:%M:%S")
                else:
                    bind_info[k] = row[k]

        return bind_info

    """
    http://initd.org/psycopg/docs/cursor.html?highlight=execute#cursor.execute
    更新绑定支付宝帐户
    """

    def bind_pay_alipay_account(self, user_id, alipay_login_account):
        sql = """INSERT INTO public.host_users_pay_account (host_id,user_id,alipay_login_account,alipay_bind_time,alipay_update_time)
                    VALUES (%(host_id)s,%(user_id)s,%(alipay_login_account)s, current_timestamp,current_timestamp)
                    ON CONFLICT (host_id,user_id)
                    DO UPDATE SET alipay_update_time = current_timestamp,alipay_login_account=%(alipay_login_account)s
                  """
        pg_cursor = self.get_pg_dict_cursor()
        pg_cursor.execute(sql,
                          {'host_id': self._host_id, 'user_id': user_id, 'alipay_login_account': alipay_login_account})
        result = pg_cursor.statusmessage
        pg_cursor.close()
        # 插入成功返回的是 INSERT 0 1
        # pg_cursor.query 是插入的sql 语句
        return True if result == 'INSERT 0 1' else False

    """
    判断 alipay 帐户是否已绑定别人
    """

    def get_alipay_account_is_bind(self, user_id, alipay_login_account):

        sql = """SELECT count(1) FROM public.host_users_pay_account 
                 WHERE host_id=%(host_id)s and user_id <> %(user_id)s and alipay_login_account = %(alipay_login_account)s
              """
        self.write_info_log('red_envelope', "dddd")
        pg_cursor = self.get_pg_dict_cursor()
        self.write_info_log('red_envelope', "ffff")
        pg_cursor.execute(sql,
                          {'host_id': self._host_id, 'user_id': user_id, 'alipay_login_account': alipay_login_account})
        row = pg_cursor.fetchone()
        pg_cursor.close()
        return False if row is None or row['count'] == 0 else True

    """
       我抢到的红包汇总，包括总条数， 总金额
    """

    def get_my_receive_red_envelope_count(self, params):
        sql = """SELECT count(1),coalesce(sum(rd.credit),0) as total_credit
                     FROM public.red_envelope_draw_record as rd 
                     JOIN public.red_envelope as r on r.id=rd.red_envelope_id 
                     JOIN public.host_users as hu on r.host_id=hu.host_id and r.user_id = hu.user_id
                    WHERE rd.host_id=%(host_id)s and rd.user_id=%(user_id)s
        		    and rd.draw_time > '%(year)s-01-01'  and rd.draw_time < '%(next_year)s-01-01'"""
        pg_cursor = self.get_pg_dict_cursor()
        params['host_id'] = self.host_id
        pg_cursor.execute(sql, params)
        row = pg_cursor.fetchone()
        return {'count': int(row['count']), 'total_credit': float(row['total_credit'])}

    """
        获取 我收的红包列表
    """

    def get_my_receive_red_envelope(self, params):
        sql = """SELECT coalesce(hu.user_name,hu.user_id) as realname, rd.credit, rd.draw_time, re.red_type ,rd.has_transfer
                        ,re.user_id || '@' || hi.host as host_user_id 
                         ,re.user_id,re.id as id
                          ,case when re.expire_time< current_timestamp then 1 else 0 end as is_expire
                          ,case when re.red_number= re.draw_number then 1 else 0 end as is_grab_over
                         FROM public.red_envelope_draw_record as rd 
                         JOIN public.red_envelope as re on re.id=rd.red_envelope_id 
                         JOIN public.host_users as hu on re.host_id=hu.host_id and re.user_id = hu.user_id
                         join public.host_info as hi on hi.id = re.host_id

                        WHERE rd.host_id=%(host_id)s and rd.user_id=%(user_id)s
                            and rd.draw_time > '%(year)s-01-01'  and rd.draw_time < '%(next_year)s-01-01' 
                        order by rd.id  desc  limit %(pagesize)s offset %(offset)s"""

        pg_cursor = self.get_pg_dict_cursor()
        params['host_id'] = self.host_id
        pg_cursor.execute(sql, params)
        rs = []
        # has_transfer = 0 超过48小时 领取额度将自动 返回支付宝
        while True:
            row = pg_cursor.fetchone()
            if row is None:
                break
            rs.append({
                'id': int(row['id']),  # 红包id
                'user_id': str(row['user_id']),  # 红包发送人
                'host_user_id': str(row['host_user_id']),  # 发送人的拼接host串
                'is_grab_over': int(row['is_grab_over']),  # 是否已抢完
                'is_expire': int(row['is_expire']),  # 是否过期
                'realname': str(row['realname']),  # 发红包的人
                'red_type': str(row['red_type']),  # 发红包的人
                'credit': float(row['credit']),  # 红包金额
                'draw_time': row['draw_time'].strftime("%Y-%m-%d %H:%M:%S"),  # 抢红包时间
            })
        pg_cursor.close()
        return rs

    """
    获取我发送的红包汇总，包括总条数， 总金额
    """

    def get_my_send_red_envelope_count(self, params):
        sql = """
                     SELECT count(1),coalesce(sum(re.credit),0) as total_credit
                      FROM public.red_envelope as re 
                      JOIN public.order_list as ol on re.order_id = ol.id
                       WHERE 
                      host_id = %(host_id)s and  user_id = %(user_id)s and ol.state <> 'unpay'
                     and re.create_time > '%(year)s-01-01'  and re.create_time < '%(next_year)s-01-01'"""
        pg_cursor = self.get_pg_dict_cursor()
        params['host_id'] = self.host_id
        pg_cursor.execute(sql, params)
        row = pg_cursor.fetchone()

        return {'count': int(row['count']), 'total_credit': float(row['total_credit'])}

    """
    获取 我发送的红包
    """

    def get_my_send_red_envelope(self, params):
        sql = """SELECT 
                  re.id,re.user_id,re.red_type,re.credit,re.balance,re.red_number,re.draw_number,re.red_content
                  ,re.user_id || '@' || hi.host as host_user_id 
                  ,re.create_time::timestamp
                  ,case when re.expire_time< current_timestamp then 1 else 0 end as is_expire
                  ,case when re.red_number= re.draw_number then 1 else 0 end as is_grab_over
                  FROM public.red_envelope as re 
                  JOIN public.order_list as ol on re.order_id = ol.id
                  join public.host_info as hi on hi.id = re.host_id
                   WHERE 
                  host_id = %(host_id)s and  user_id = %(user_id)s and ol.state <> 'unpay'
                 and re.create_time > '%(year)s-01-01'  and re.create_time < '%(next_year)s-01-01' 
                 ORDER BY re.id desc limit %(pagesize)s offset %(offset)s"""
        pg_cursor = self.get_pg_dict_cursor()
        params['host_id'] = self.host_id
        pg_cursor.execute(sql, params)
        rs = []
        while True:
            row = pg_cursor.fetchone()
            if row is None:
                break
            rs.append({
                'id': int(row['id']),  # id 红包id
                'user_id': str(row['user_id']),  # 红包发送人
                'host_user_id': str(row['host_user_id']),  # 红包发送人拼接host
                'red_type': str(row['red_type']),  # 红包类型
                'credit': float(row['credit']),  # 红包金额
                'balance': float(row['balance']),  # 红包剩余金额

                'is_grab_over': int(row['is_grab_over']),  # 是否已抢完
                'is_expire': int(row['is_expire']),  # 是否过期
                'red_number': int(row['red_number']),  # 总红包个数
                'draw_number': int(row['draw_number']),  # 已抢红包个数
                'red_content': str(row['red_content']),  # 红包内容
                'create_time': row['create_time'].strftime("%Y-%m-%d %H:%M:%S"),  # 发红包时间
                'create_date': row['create_time'].strftime("%Y-%m-%d"),  # 发红包时间
            })
        pg_cursor.close()
        return rs
