#!/usr/bin/env python
# -*- coding:utf-8 -*-


# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
红包相关sql 继承common_sql.UserLib

# psycopg2.extras.register_json(oid=3802, array_oid=3807, globally=True)
# psycopg2.extras.register_default_jsonb()

"""
import asyncpg

__author__ = 'jingyu.he'

import psycopg2.extras
from utils.common_sql import UserLib, sql_logger, redis_cli
from service.red_envelope.common import *
from utils.logger_conf import configure_logger
from utils.aa_rounding import *

# http://initd.org/psycopg/docs/extras.html#connection-and-cursor-subclasses
psycopg2.extras.register_default_json(loads=lambda x: x)
psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)

"""
红包相关sql 继承common_sql.UserLib 
"""
domain = r_domain


class AllAverageSql(UserLib):
    def __init__(self):
        super().__init__()

        self._all_average_logger = configure_logger("all_average")
        self._order_list_logger = configure_logger("order_list")

        self._host_id = None
        # 设置host id
        if domain:
            self.set_host_id(domain[0])

    """
    注意写日志，一定要写红包id, 订单id
    """

    def write_info_log(self, log_type, message):
        if log_type == 'all_average':
            self._all_average_logger.info(message)
        elif log_type == 'order_list':
            self._order_list_logger.info(message)

    """
      注意写日志一定要写红包id, 订单id
    """

    def write_error_log(self, log_type, message):
        if log_type == 'all_average':
            self._all_average_logger.error(message)
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

        # sql = "SELECT id as host_id FROM public.host_info WHERE host_id=%(host_id)s limit 1;"
        sql = """SELECT id as host_id FROM public.host_info WHERE host=%(host_id)s limit 1"""
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
        user = user_id
        if '@' in user_id:
            user = user_id.split('@')[0]
            user_domain = user_id.split('@')[1]
        sql = """SELECT id,alipay_login_account,alipay_bind_time ,alipay_update_time FROM 
              public.host_users_pay_account WHERE host_id=%(host_id)s and user_id = %(user_id)s
              """
        self.write_info_log('all_average', "dddd111")
        pg_cursor = self.get_pg_dict_cursor()
        self.write_info_log('all_average', "dddd1222")
        pg_cursor.execute(sql, {'host_id': self._host_id, 'user_id': user})
        self.write_info_log('all_average', "dddd1333")
        row = pg_cursor.fetchone()
        self.write_info_log('all_average', "dddd14444")
        pg_cursor.close()
        self.write_info_log('all_average', "5555")
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
        self.write_info_log('all_average', "dddd")
        pg_cursor = self.get_pg_dict_cursor()
        self.write_info_log('all_average', "ffff")
        pg_cursor.execute(sql,
                          {'host_id': self._host_id, 'user_id': user_id, 'alipay_login_account': alipay_login_account})
        row = pg_cursor.fetchone()
        pg_cursor.close()
        return False if row is None or row['count'] == 0 else True

    """
       我发起的aa收款，包括群名、内容、总金额、收款状态、发起时间
       OFFSET 0 LIMIT 20
       TODO
    """

    def get_my_organize_aa(self, params):
        # sql = """SELECT count(1),coalesce(sum(rd.credit),0) as total_credit
        #              FROM public.all_average_draw_record as rd
        #              JOIN public.all_average as r on r.id=rd.all_average_id
        #              JOIN public.host_users as hu on r.host_id=hu.host_id and r.user_id = hu.user_id
        #             WHERE rd.host_id=%(host_id)s and rd.user_id=%(user_id)s
        # 		    and rd.draw_time > '%(year)s-01-01'  and rd.draw_time < '%(next_year)s-01-01'"""
        sql = """SELECT * FROM public.all_average as aa WHERE aa.organizer_id = %(user_id)s and aa.host_id = %(host_id)s and aa.create_time > '%(year)s-01-01' and aa.create_time < '%(year)s-01-01' OFFSET 0 LIMIT 20"""
        pg_cursor = self.get_pg_dict_cursor()
        params['host_id'] = self.host_id
        pg_cursor.execute(sql, params)
        row = pg_cursor.fetchone()
        return {'count': int(row['count']), 'total_credit': float(row['total_credit'])}

    """
        我参与的aa收款 需要聚合all_average_draw_record中的内容
        TODO
    """

    def get_my_paid_all_average(self, params):
        sql = """SELECT coalesce(hu.user_name,hu.user_id) as realname, rd.credit, rd.draw_time, re.red_type ,rd.has_transfer
                        ,re.user_id || '@' || hi.host as host_user_id 
                         ,re.user_id,re.id as id
                          ,case when re.expire_time< current_timestamp then 1 else 0 end as is_expire
                          ,case when re.red_number= re.draw_number then 1 else 0 end as is_grab_over
                         FROM public.all_average_draw_record as rd 
                         JOIN public.all_average as re on re.id=rd.all_average_id 
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
    TODO
    """

    def get_all_average_detail(self, params):
        sql = """
                     SELECT count(1),coalesce(sum(re.credit),0) as total_credit
                      FROM public.all_average as re 
                      JOIN public.order_list as ol on re.order_id = ol.id
                       WHERE 
                      host_id = %(host_id)s and  user_id = %(user_id)s and ol.state <> 'unpay'
                     and re.create_time > '%(year)s-01-01'  and re.create_time < '%(next_year)s-01-01'"""
        sql = """ SELECT * FROM all_average WHERE """
        pg_cursor = self.get_pg_dict_cursor()
        params['host_id'] = self.host_id
        pg_cursor.execute(sql, params)
        row = pg_cursor.fetchone()

        return {'count': int(row['count']), 'total_credit': float(row['total_credit'])}

    """
    获取 我发送的红包
    """

    def get_my_send_all_average(self, params):
        sql = """SELECT 
                  re.id,re.user_id,re.red_type,re.credit,re.balance,re.red_number,re.draw_number,re.red_content
                  ,re.user_id || '@' || hi.host as host_user_id 
                  ,re.create_time::timestamp
                  ,case when re.expire_time< current_timestamp then 1 else 0 end as is_expire
                  ,case when re.red_number= re.draw_number then 1 else 0 end as is_grab_over
                  FROM public.all_average as re 
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

    def create_all_average(self, params):
        print("准备创建aa.. ")
        required_params = {
            "host_id": self._host_id,
            "organizer": params.get('user_id'),
            "details": params.get('details'),
            "aa_type": params.get('aa_type'),
            "credit": params.get('credit'),
            "amount": params.get('amount'),
            "paid_number": params.get('paid_number'),
            "aa_number": params.get('aa_number'),
            "aa_content": params.get('aa_content'),
            "expire_time": params.get('expire_time'),
            "group_chat_id": params.get('group_chat_id'),
            "create_time": params.get('create_time'),
            "members": params.get('members'),
            "payee_account": params.get('payee_account'),
        }
        atype = required_params.get('aa_type')

        conn = self.conn
        sql = """insert into public.all_average 
                        (host_id, organizer, aa_type, credit, amount, aa_number, paid_number, aa_content,
                        expire_time, group_chat_id, create_time, members, payee_account)
                         values (%(host_id)s,%(organizer)s,%(aa_type)s,%(credit)s,%(amount)s,%(aa_number)s,
                         %(paid_number)s,%(aa_content)s,%(expire_time)s,%(group_chat_id)s,%(create_time)s, 
                         %(members)s, %(payee_account)s)
                  RETURNING id as id
              """
        print("正在创建aa 参数 {}".format(required_params))
        cursor = conn.cursor()
        print(" !!!! {} ".format(required_params))
        cursor.execute(sql, required_params)
        rs = cursor.fetchall()
        all_average_id = None
        if len(rs) > 0:
            all_average_id = rs[0][0]
            required_params['all_average_id'] = all_average_id

        sql = """insert into public.all_average_draw_record (host_id, payer, all_average_id, credit) values {value}"""
        sqls = []
        organizer = required_params['organizer']
        organizer_p = False

        if atype == 'custom':
            for payer, money in required_params.get('details', {}).items():
                if payer.split('@')[0] == organizer:
                    organizer_p = True
                sqls.append("""(%(host_id)s, '{}', %(all_average_id)s, {})""".format(
                    payer, money))
            sql = sql.format(value=','.join(sqls))
        elif atype == 'normal':
            money = cal_avg_credit(num=required_params.get('aa_number'), credit=required_params.get('credit'))
            for payer in required_params.get('details', ):
                if payer.split('@')[0] == organizer:
                    organizer_p = True
                sqls.append("""(%(host_id)s, '{}', %(all_average_id)s, {})""".format(
                    payer, money))
            sql = sql.format(value=','.join(sqls))
        else:
            print("WRONG AA_TYPE {}".format(params))
        cursor.execute(sql, {'host_id': required_params.get('host_id'),
                             'all_average_id': required_params.get('all_average_id')})

        if organizer_p:
            sql = """update public.all_average_draw_record SET has_transfer = 1, paid_time = current_timestamp, transfer_time = current_timestamp where all_average_id = %(aid)s and payer = %(organizer)s"""
            cursor.execute(sql, {'aid': all_average_id,
                                 'organizer': organizer})
        cursor.close()

        return all_average_id

    def get_user_order(self, user_id, aa_id):
        pass

    def get_aa_payee(self, order_no):
        conn = self.conn
        sql = """select payee_account from all_average where id = (select aid as account from public.order_list where order_no = %(order_no)s limit 1)"""
        cursor = conn.cursor()
        cursor.execute(sql, {"order_no": order_no})
        rs = cursor.fetchall()
        cursor.close()
        if not len(rs):
            return None
        if len(rs[0]):
            return rs[0][0]
        else:
            return None

    def get_payment(self, user_id, aid):
        credit = None
        conn = self.conn
        sql = """select credit from all_average_draw_record where all_average_id = %(aid)s and payer = %(user_id)s"""
        cursor = conn.cursor()
        cursor.execute(sql, {"aid": aid, "user_id": user_id})
        rs = cursor.fetchall()
        if len(rs) > 0:
            credit = rs[0][0]
        cursor.close()
        return credit

    def update_payer_order(self, aid, user_id, order_id, order_line):
        conn = self.conn
        sql = """update public.all_average_draw_record SET order_id = %(order_id)s, transfer_order_line = %(order_line)s where all_average_id = %(aid)s and payer = %(user_id)s"""
        cursor = conn.cursor()
        try:
            cursor.execute(sql, dict(aid=aid, user_id=user_id, order_id=order_id, order_line=order_line))
        except Exception as e:
            print(e)
            return False
        finally:
            cursor.close()
        return True

    def check_user_identify(self, aid: int, user_id: str):
        conn = self.conn
        sql = """select members from public.all_average where id = %(aid)s """
        cursor = conn.cursor()
        cursor.execute(sql, {"aid": aid})
        rs = cursor.fetchall()
        members = {}
        if len(rs) > 0:
            members = rs[0][0]
        cursor.close()
        if user_id in members.keys():
            return True
        else:
            print("用户aa鉴权失败")
            return False

    def get_aa_status(self, aid):
        ret = {
            "type": "",  # normal / custom
            "content": "",
            "aa_status": 0,  # 0：未收齐， 1：已收齐， 2：已过期
            "summary": 0.00,
            "incoming": 0.00,
            "organizer": "",
            "detail": {}
        }
        conn = self.conn
        sql = """select id, organizer, aa_type, credit, amount, aa_content, status from public.all_average where id = %(aid)s """
        cursor = conn.cursor()
        cursor.execute(sql, {"aid": aid})
        rs = cursor.fetchall()
        if len(rs) > 0 and len(rs[0]) == 7:
            ret["id"] = rs[0][0]
            ret["organizer"] = rs[0][1]
            ret["type"] = rs[0][2]
            ret["summary"] = rs[0][3]
            ret["incoming"] = rs[0][4]
            ret["content"] = rs[0][5]
            ret["aa_status"] = rs[0][6]
        else:
            print("没有相关的aa信息")
            cursor.close()
            return {}
        sql = """select payer, credit, has_transfer  from all_average_draw_record where all_average_id = %(aid)s"""
        cursor = conn.cursor()
        cursor.execute(sql, {"aid": aid})
        rs = cursor.fetchall()
        cursor.close()
        detail = []
        if len(rs) > 0:
            for _s in rs:
                detail.append(dict(user=_s[0], has_transfer=_s[1], credit=_s[2]))
        ret['detail'] = detail
        return ret

    def pay_success_callback(self, order_no: str):

        conn = self.conn
        sql = """select aid, pay_account from public.order_list where order_no = %(order_no)s"""
        # sql = """select all_average_id as aid, payer as user_id from public.all_average_draw_record where transfer_order_line = %(order_no)s"""
        cursor = conn.cursor()
        cursor.execute(sql, {"order_no": order_no})
        rs = cursor.fetchall()
        if len(rs) == 1:
            aid = rs[0][0]
            pay_account = rs[0][1]
        else:
            print("付款回调未找到红包")
            return False
        sql = """select a.user_id || '@' || b.host from host_users_pay_account as a right join host_info as b on a.alipay_login_account= %(pay_account)s; """
        cursor.execute(sql, {"pay_account": pay_account})
        rs = cursor.fetchall()

        if len(rs) == 1:
            user_id = rs[0][0]
        else:
            print("查询付款用户出错 查询结果： {}".format(rs))
            return False

        # 更新all_average 余额等信息
        sql = """update
                   public.all_average
                 set
                   amount = amount + (
                     select
                       credit
                     from
                       public.all_average_draw_record
                     where
                       all_average_id = %(aid)s
                       and payer = %(user_id)s
                   ),
                   paid_number = paid_number + 1,
                   update_time = now(),
                   status = 
                     Case
                         WHEN paid_number = aa_number - 1 THEN 2
                         ELSE 1
                     END
                 where id = %(aid)s returning id"""
        cursor.execute(sql, {"aid": aid, "user_id": user_id})
        rs = cursor.fetchall()
        if not len(rs):
            print("更新all_average失败")
            return False

        sql = """update public.all_average_draw_record set 
        transfer_time = now(),
        transfer_order_line = %(order_no)s,
        has_transfer = 1
        where all_average_id = %(aid)s and payer = %(payer)s
        returning all_average_id
        """
        cursor.execute(sql, {"aid": aid, "order_no": order_no, "payer": user_id})
        rs = cursor.fetchall()
        if not len(rs):
            print("更新all_average失败")
            return False
        cursor.close()
        print("状态更新成功")
        return True

    def check_user(self, aid, user_id):
        ret = {"ret": False, "error_message": ""}
        conn = self.conn
        if len(user_id) < 2 or int(aid) <= 0:
            ret['error_message'] = "错误的参数 aid {} user_id {}".format(aid, user_id)
            return ret
        sql = """select payer from all_average_draw_record where all_average_id = %(aid)s"""
        cursor = conn.cursor()
        cursor.execute(sql, {"aid": aid})
        rs = cursor.fetchall()
        cursor.close()
        if len(rs) == 0:
            ret['error_message'] = "未找到aa aid {} ".format(aid)
            return ret
        for u in rs:
            if len(u) > 0 and u[0] == user_id:
                ret['ret'] = True
                return ret
        ret['error_message'] = "用户无权查看红包 aid {} user_id {}".format(aid, user_id)
        return ret

    def get_aa_detail(self, aid, user_id):
        user_data = {
            "credit": 0,  # 抢的金额
            "has_transfer": 0,  # 是否已转帐
            "user_id": "",  # 抢的人
            "user_img": "",  # 抢的人的头像
            "user_name": ""  # 抢的真实姓名
        }
        data = {
            "user_status": 2,  # 0 未支付 1 已支付 2 无关
            "paid_money": 0,  # 需付款金额,
            "need_paid": 0,
            "create_time": None,  # aa创建时间
            "total": 0,  # aa总金额
            "paid_number": 0,  # 已抢的个数 , 包含发起者本身
            "unpaid_number": 0,  # 已抢的个数
            "payer_record": [],  # aa支付人信息,
            "aa_content": "",  # aa内容
            "aa_number": 0,  # aa个数
            "aa_type": "normal",  # aa类型  normal | customized
            "payee_id": "",  # 发红包的人
            "payee_img": "",  # 头像
            "payee_name": ""  # 发红包的真实姓名
        }
        inter_params = {
            "host_id": "",
            "members": {},
            "host_name": ""
        }
        ret = {"ret": False, "error_message": "", "data": {}}
        user = user_id.split('@')[0] if '@' in user_id else user_id
        conn = self.conn
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        sql = """select hi.id as host_id, hi.host as host_name, aa.create_time as create_time, aa.organizer||'@'||hi.host as payee_id, members as members, aa_type as aa_type, credit as credit, 
                 cast(credit as float) as total, aa_number as aa_number, paid_number as paid_number, (aa.aa_number - aa.paid_number) as unpaid_number,
                 aa_content as aa_content, cast(amount as float) as paid_money from public.all_average as aa inner join host_info as hi on aa.id = %(aid)s and aa.host_id = hi.id"""
        cursor.execute(sql, {"aid": aid})
        rs = cursor.fetchall()
        print("{}".format(rs))
        if len(rs) > 0:
            if isinstance(rs[0], dict):
                for k, v in rs[0].items():
                    if k in data.keys():
                        if k == 'create_time':
                            v = v.strftime("%Y-%m-%d %H:%M:%S")
                        data[k] = v
                inter_params["host_id"] = int(rs[0]['host_id'])
                inter_params["members"] = rs[0]['members']
                inter_params["host_name"] = rs[0]['host_name']

            else:
                print("warning， 不是dict {}".format(rs))
        else:
            ret["error_message"] = "无法获取aa信息"
            return ret

        sql = """select hu.user_name as payee_name, vv.url as payee_img from host_users as hu inner join public.vcard_version as vv 
                 on vv.username = %(user_id)s and hu.user_id = %(user_id)s and vv.host = %(host_name)s and hu.host_id = %(host_id)s"""
        cursor.execute(sql, {"user_id": data['payee_id'].split('@')[0], "host_name": inter_params["host_name"],
                             "host_id": inter_params["host_id"]})
        rs = cursor.fetchall()
        if len(rs) > 0:
            if isinstance(rs[0], dict):
                for k, v in rs[0].items():
                    if k in data.keys():
                        data[k] = v
            else:
                print("warning， 不是dict {}".format(rs))
        else:
            ret["error_message"] = "无法获取用户信息"
            return ret
        inter_params['members'] = inter_params['members'][1:-1].split(',') if inter_params['members'] else []
        sql = """select
                  vv.url as user_img,
                  hu.user_id as user_id,
                  hu.user_name as user_name,
                  aadr.payer as user_id,
                  cast(aadr.credit as float) as credit,
                  aadr.has_transfer as has_transfer
                from
                  (
                    all_average_draw_record as aadr
                    inner join host_users as hu on aadr.all_average_id = %(aid)s
                    and aadr.payer = ANY(%(members)s)
                    and split_part(aadr.payer, '@', 1) = hu.user_id
                  )
                  INNER JOIN vcard_version as vv ON vv.username = hu.user_id"""
        cursor.execute(sql, {"aid": aid, "members": inter_params["members"]})
        rs = cursor.fetchall()
        if len(rs) > 0:
            temp = []
            for user in rs:
                temp_data = user_data.copy()
                if isinstance(user, dict):
                    for k, v in user.items():
                        if k in temp_data.keys():
                            temp_data[k] = v
                    temp.append(temp_data)
                    print("!!! {}".format(temp))
                else:
                    print("warning， 不是dict {}".format(user))
            data['payer_record'] = temp
        else:
            ret["error_message"] = "无法获取支付详情"
            return ret
        print("获取信息完成 {}".format(data))
        for u in data['payer_record']:
            if u['user_id'] == user_id:
                data['need_paid'] = u['credit']
        print("user id {} members {}".format(user_id, inter_params['members']))
        print("record {}".format(data['payer_record']))
        if user_id in inter_params['members']:
            for __user in data['payer_record']:
                if __user['user_id'] == user_id:
                    if __user['has_transfer'] == 1:
                        data['user_status'] = 1
                    elif __user['has_transfer'] == 0:
                        data['user_status'] = 0
        ret = {"ret": True, "error_message": "", "data": data}
        return ret
