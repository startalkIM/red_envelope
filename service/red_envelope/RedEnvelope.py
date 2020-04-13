#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
红包 入库相关操作
"""
import random
import sys
import time
import datetime
import traceback

import math

from decimal import Decimal

from service.red_envelope.common import *
from service.red_envelope.common_sql import RedEnvelopeSql


"""
使用redenvelope类 必须使用try excpt 

    try:
        rel = RedEnvelope({"id":1})
        return display_json("e")
    except Exception as e:
        return display_json(str(e))
        
        
"""


class RedEnvelope:

    # 错误码
    error_code = {
        "4001": "id的格式错误",
        "4002": "红包不存在",
        "4003": "数据库执行失败",
        "4004": "缓存失败",
        "4005": "红包已过期",
        "4006": "你已领取该红包",
        "4007": "红包已抢光",
        "4008": "未登录",
        "4009": "参数出错",
        "4010": "红包金额不能超过99999",
        "4011": "订单红包已存在",
        "4021": "鉴权失败",
        "4022": "非法访问",
        "4023": "不支持的支付方式",
        "4030": "今日抢同一发送用户红包超限",
        "4300": "用户未绑定支付宝",
    }

    def __init__(self, **params):
        self._rels = RedEnvelopeSql()
        self._table_fields = ["id", "host_id", "user_id", "red_type", "credit", "balance", "red_number", "draw_number",
                              "red_content", "order_id", "expire_time", "group_chat_id", "create_time", "update_time"]

        self.redis_cli = self._rels.get_redis_conn()
        names = self.__dict__
        for k in self._table_fields:
            names[k] = ""

        # 必须是个字典
        if type(params) is not dict:
            # 传参错误
            self.write_info_log("红包id%s:4009：%s" % (str(params['id']), str(self.error_code['4009'])))
            raise Exception('4009')

        # 覆盖传进来的所有充数量值 上边定义的
        names = self.__dict__
        for k in names:
            if k in params.keys():
                names[k] = params[k]

        # 处理id 预处理变量 放最后处理， 会覆盖变量
        id_key = ""
        if "id" in params.keys() and 'user_id' not in params.keys():
            id_key = "id"
        elif "order_id" in params.keys() and 'user_id' not in params.keys():
            id_key = "order_id"

        if id_key:

            if type(params[id_key]) is not int or params[id_key] <= 0:
                # id的格式错误
                self.write_info_log("红包%s%s:4001：%s" % (id_key, str(params[id_key]), str(self.error_code['4001'])))
                raise Exception("4001")
            self.write_info_log("红包%s%s:初始化" % (id_key, str(params[id_key])))
            if id_key =='id':
                res = self.get_info(red_id=params['id'])
            else:
                res = self.get_info(order_id=params['order_id'])

            info = res['data']
            if not res['ret'] or not info or info[id_key] != params[id_key]:
                # 红包不存在
                self.write_info_log("红包%s%s:4002：%s" % (id_key, str(params[id_key]), str(self.error_code['4002'])))
                raise Exception("4002")
            # 重写 所有的变量值
            names = self.__dict__
            for k in info:
                names[k] = info[k]
            self.write_info_log("红包%s%s:所有信息:%s" % (id_key, str(params[id_key]), json.dumps(info, ensure_ascii=False)))


    """
    获取当天 某用户 抢同一用户的 红包数
    """
    def get_day_grab_count(self, host_id, send_user_id, grab_user_id):

        sql = """SELECT count(1)
                  FROM public.red_envelope_draw_record redr
                       join public.red_envelope as re on redr.red_envelope_id = re.id 
                 where re.host_id = '%s' and re.user_id ='%s' and redr.user_id = '%s' and redr.draw_time::date = current_date
            """ % (host_id, send_user_id, grab_user_id)
        cursor = self._rels.get_pg_dict_cursor()
        try:
            cursor.execute(sql)
            row = cursor.fetchone()
        except Exception as e:
            row = None
            sql_error = str(cursor.query) + " error: " + str(e) + ",trace:" + traceback.format_exc()
            return self.return_result(ret=False,
                                      data={"id": self.id},
                                      error_code=4003,
                                      error_msg="数据库执行失败",
                                      sql_error=sql_error
                                      )
        finally:
            cursor.close()

        return int(row['count'])

    """
    根据id | order_id 获取一条红包信息
    """
    def get_info(self, red_id: int = None, order_id: int = None):
        cursor = self._rels.get_pg_dict_cursor()

        condition = ' 1=1 '
        if red_id:
            condition += " AND re.id='%d'" % red_id
        elif order_id:
            condition += " AND re.order_id='%d'" % order_id
        else:
            # 直接false 即可
            condition += " AND 1=2 "
        sql = """select 
                    re.*,hu.user_name ,re.user_id || '@' || hi.host as host_user_id,hi.host
                    ,case when re.expire_time< current_timestamp then 1 else 0 end as is_expire
                  ,case when re.red_number= re.draw_number then 1 else 0 end as is_grab_over
                from public.red_envelope as re
                 join public.host_info as hi on hi.id = re.host_id
                left join public.host_users as hu on re.host_id = hu.host_id and re.user_id = hu.user_id
               where %s""" % condition

        try:
            cursor.execute(sql)
            row = cursor.fetchone()
        except Exception as e:
            row = None
            sql_error = str(cursor.query) + " error: " + str(e) + ",trace:" + traceback.format_exc()
            return self.return_result(ret=False,
                                      data={"id": self.id},
                                      error_code=4003,
                                      error_msg="数据库执行失败",
                                      sql_error=sql_error
                                      )
        finally:
            cursor.close()

        info = {}
        for k in self._table_fields:
            info[k] = ""
        info['host'] = ""
        info['user_name'] = ""
        info['is_expire'] = 0
        info['is_grab_over'] = 0
        info['host_user_id'] = ""

        if row is not None:
            for k in info:
                if k in ['create_time', 'update_time', 'expire_time']:
                    # timestamp 格式出来的是date time (Mon, 03 Jun 2019 11:02:24 GMT)需要转换一下格式用于显示
                    if type(row[k]) is not None:
                        info[k] = row[k].strftime("%Y-%m-%d %H:%M:%S")
                elif k in ["credit", "balance"]:
                    info[k] = float(row[k])
                elif k in ["red_number", "draw_number", "order_id", "id", "host_id"]:
                    info[k] = int(row[k])
                else:
                    info[k] = row[k]

        return self.return_result(ret=True, data=info)

    def generate_sub_redenv(self):
        """生成小红包，以及redis缓存队列"""

        cursor = self._rels.get_pg_dict_cursor()

        balance = Decimal(self.credit)
        # data = []
        ext_sql = ""

        for i in range(self.red_number):
            info = {
                'red_type': self.red_type,
                'red_number': self.red_number,
                'draw_number': i,
                'balance': balance,
                'credit': self.credit
            }
            current_credit = self.get_current_draw_credit(**info)
            balance -= current_credit
            # data.append((self.host_id, self.id, decimal_2_float(current_credit,2)))
            ext_sql += "(%s,%s,%s)," % (self.host_id, self.id, decimal_2_float(current_credit, 2))

        ext_sql = ext_sql.rstrip(",")
        sql = "Insert into public.red_envelope_draw_record(host_id, red_envelope_id, credit) values "+ext_sql + " Returning id;"
        try:
            cursor.execute(sql)
            result_list = cursor.fetchall()
        except Exception as e:
            sql_error = str(cursor.query) + " error: " + str(e) + ",trace:" + traceback.format_exc()
            self.write_info_log("数据库执行失败,详细信息：%s" % (sql_error,))
            return {
                "ret": False,
                "error_msg": "数据库执行失败"
            }
        finally:
            cursor.close()

        rkey = self.get_redis_key(self.id, "remain_queue")
        pipe = self.redis_cli.pipeline()
        pipe.multi()
        if result_list:
            for sub_rid in result_list:
                pipe.rpush(rkey, sub_rid['id'])
            expire_time = datetime.datetime.strptime(self.expire_time, '%Y-%m-%d %H:%M:%S')
            pipe.expireat(rkey, expire_time)
        result = pipe.execute()
        if not result:
            self.write_info_log("生成小红包redis队列失败,红包id为%s" % (self.id, ))
            return {
                "ret": False,
                "error_msg": "红包生成失败"
            }

        return {
            "ret": True
        }

    def get_current_draw_credit(self, **kwargs):
        """检查参数合法行"""

        balance = kwargs['balance']
        if isinstance(balance, float):
            balance = Decimal(balance)
        credit = kwargs['credit']
        if isinstance(credit, float):
            credit = Decimal(credit)

        if kwargs['red_number'] <= kwargs['draw_number']:
            return Decimal(0.00)
        else:
            if kwargs['red_type'] == 'lucky':
                remain_number = kwargs['red_number'] - kwargs['draw_number']
                if remain_number == 1:
                    amount = balance
                else:
                    aver = math.floor(balance * 100 / remain_number)
                    amount = random.randint(1, aver * 2 - 1) / 100
            else:
                amount = round(credit / kwargs['red_number'], 2)

            return Decimal(amount)

    """
    获取 redis 缓存的key 主键 
    *命名规范：表名＋＂:＂+ 主键值 + "列名"
    red_id = 红包的id
    
    已知子key 
    获取红包相关的 redis key 值
    remain_number  # 剩余红包数 用于发送已领红包消息用 计数器，初始值同 red_number 红包个数， 当抢完发送完qtalk消息时 执行 redis.decr 减1操作
    grab_record  # 抢红包已抢的列表 用于判断自已是否抢了
    remain_queue  # 等抢的小红包队列
    info   # 红包 整体信息 json格式
    
    已知redis key 如下：
    红包组合的 redis key 
    red_envelope:101:info 红包基本信息 
    red_envelope:101:remain_number 红包剩余数量
    red_envelope:101:remain_queue  红包待抢小红包列表
    red_envelope:101:grab_record  红包已抢记录 存储 host_id user_id 
    
    红包相关qtalk 发消息队列
    red_envelope:qtalk_message_queue 消息value json 格式，取出需 json.loads(x, ensure_ascii=False)
     
    """

    def get_redis_key(self, red_id, column=None):
        if not column:
            # 整体红包的key 值
            return "red_envelope:%s" % red_id
        else:
            # 红包下某key 的值
            return "red_envelope:%s:%s" % (red_id, column)

    """
    缓存红包信息
    只有创建红包时才初始化一次
    red_id 红包id
    only_info  是否只更新info信息， 如果为True 则只更新info ， 否则更新 剩余红包 
    """
    def cache_red_info(self, red_id: int, only_info=False):
        res = self.get_info(red_id)
        info = res['data']
        if not res['ret'] or not info or str(info['id']) != str(red_id):
            return False

        # 红包基本信息
        red_info_key = self.get_redis_key(red_id=red_id, column="info")

        self.redis_cli.set(red_info_key, json.dumps(info, ensure_ascii=False))

        if not only_info:
            # 剩余红包数 用于发送已领红包消息用
            red_remain_number_key = self.get_redis_key(red_id=red_id, column="remain_number")
            self.redis_cli.set(red_remain_number_key, info['red_number'])

            self.redis_cli.expireat(red_remain_number_key,
                                    datetime.datetime.strptime(info['expire_time'], "%Y-%m-%d %H:%M:%S"))

        # 此处过期时间使用 红包的 过期时间，而不使用 pay_config['red_envelope']['expiry_time']
        self.redis_cli.expireat(red_info_key, datetime.datetime.strptime(info['expire_time'], "%Y-%m-%d %H:%M:%S"))

        return True

    """
    获取 红包信息
    """

    def get_red_info_from_cacheordb(self, red_id: int):
        red_cache_key = self.get_redis_key(red_id)
        info = self.redis_cli.hget(red_cache_key, "info")
        if info is not None:
            info = json.loads(info)
        else:
            res = self.get_info(red_id=red_id)
            info = res['data']
            if not res['ret'] or not res['data']:
                return None

        if str(info['id']) != str(red_id):
            return None
        return info

    """
    发红包 ，只生成红包记录
    """
    def create(self):
        self.write_info_log("红包id%s:创建红包初始化;" % self.id)

        if len(str(self.id)) > 0 and str(self.id) != "0":
            # 红包已经存在
            return self.return_result(**{"ret": 0,
                                         "data": {"id": self.id},
                                         "error_code": 4011,
                                         "error_msg": self.error_code['4011'],
                                         "sql_error": ""})

        self_id_tmp = self.id
        # 根据order_id 查找红包是否存在
        red_info_res = self.get_info(order_id=self.order_id)
        red_info = red_info_res['data']
        if red_info_res['ret'] and red_info and  str(red_info['id']) != "":
            # 红包已经存在
            return self.return_result(**{"ret": 0,
                                         "data": {"id": 0},
                                         "error_code": 4011,
                                         "error_msg": self.error_code['4011'],
                                         "sql_error": ""})

        sql = """insert into public.red_envelope 
                        (host_id,user_id,red_type,credit,balance,red_number,draw_number,red_content,order_id,expire_time,group_chat_id,create_time)
                         values (%(host_id)s,%(user_id)s,%(red_type)s,%(credit)s,%(balance)s,%(red_number)s,
                         %(draw_number)s,%(red_content)s,%(order_id)s,%(expire_time)s,%(group_chat_id)s,%(create_time)s)
                  RETURNING id
              """
        params = {
                    "host_id": self.host_id,
                    "user_id": self.user_id,
                    "red_type": self.red_type,
                    "credit": self.credit,
                    "balance": self.balance,
                    "red_number": self.red_number,
                    "draw_number": self.draw_number,
                    "order_id": self.order_id,
                    "red_content": self.red_content,
                    "expire_time": self.expire_time,
                    "group_chat_id": self.group_chat_id,
                    "create_time": self.create_time
                  }

        self.write_info_log("红包id%s:获取参数:%s" % (self.id, json.dumps(params, ensure_ascii=False)))
        pg_cursor = self._rels.get_pg_dict_cursor()

        sql_error = ""
        # execute sql语句只要有错误 就会触发异常
        try:
            pg_cursor.execute(sql, params)
            row = pg_cursor.fetchone()
            if row is not None:
                self.id = row['id']
            self.write_info_log("红包id%s:生成新红包成功" % (self.id))
        except Exception as e:
            self.write_info_log("订单id%s:生成新语句,%s" % (self.id, str(pg_cursor.query)))
            result = str(e)
            sql_error = " error: " + result + ",trace:" + str(traceback.format_exc())
        pg_cursor.close()

        # pg_cursor.query 是插入的sql 语句
        if str(self.id) != "":
            return self.return_result(**{"ret": 1,
                                         "data": {"id": self.id},
                                         "error_code": 200,
                                         "error_msg": "",
                                         "sql_error": sql_error})
        else:
            self.id = self_id_tmp
            return self.return_result(**{"ret": 0,
                                         "data": {"id": self.id},
                                         "error_code": 4003,
                                         "error_msg": "数据库执行失败",
                                         "sql_error": sql_error})

    """
    返回结果格式化的结果
    """

    def return_result(self, **params):
        if type(params) is not dict:
            params = dict()
        ret = int(params['ret']) if 'ret' in params.keys() else 0
        data = params['data'] if 'data' in params.keys() else dict()
        error_code = int(params['error_code']) if 'error_code' in params.keys() else 0
        error_msg = params['error_msg'] if 'error_msg' in params.keys() else ""
        sql_error = params['sql_error'] if 'sql_error' in params.keys() else ""

        if len(sql_error) > 0:
            self._rels.write_error_log(log_type="red_envelope",
                                       message=""""ret:%s,data:%s,error_code:%s,error_msg:%s,sql_error:%s""" %
                                               (str(ret), str(data), str(error_code), str(error_msg),
                                                str(sql_error)))
        else:
            self.write_info_log(json.dumps(params, ensure_ascii=False))
        return {
            "ret": ret,
            "data": data,
            "error_code": error_code,
            "error_msg": error_msg
        }

    """
    写日志
    """

    def write_info_log(self, message):
        self._rels.write_info_log(log_type="red_envelope", message=message)

    """
    检测 是否有抢红包的权限
    group_id 用户参数 传过来的
    group_chat_id 红包的group_chat_id
    """

    def check_power(self, group_id, group_chat_id):
        if not isinstance(group_chat_id, list):
            return False
        return group_id in group_chat_id

    """
    检测 红包的过期时间是否过期
    expire_time 红包的过期时间 字符串型式
    """

    def check_expired(self, expire_time):
        try:
            et = time.mktime(time.strptime(expire_time, "%Y-%m-%d %H:%M:%S"))
        except Exception as e:
            return True

        return True if et < time.time() else False

    """
    检测 红包是否已抢光
    red_number 红包的数量
    draw_number 已抢的红包数量
    
    写小红包操作
    lkey = rel.get_redis_key("101", "remain_queue")
    redis_cli.rpush(lkey, srid) # srid 即小红包id
    """
    def check_is_out(self, red_id: int):
        #  待抢红包队列
        lkey = self.get_redis_key(red_id, "remain_queue")

        return True if self.redis_cli.llen(lkey) == 0 else False

    """
    自已是否抢过 只有在红包未过期时 才会有， 抢红包时 自动写到缓存中去
    host_id 域id
    user_id 用户id
    red_id 红包id
    """
    def check_is_grab(self, host_id: int, user_id, red_id: int):
        red_cache_key = self.get_redis_key(red_id, column="grab_record")
        cache_column = "%s:%s" % (host_id, user_id)
        info = self.redis_cli.hget(red_cache_key, cache_column)

        return True if info else False

    """
    抢红包成功时 要设置 已抢过的缓存
    host_id 域id
    user_id 用户id
    red_id 抢红包id
    """
    def set_grab_cache(self, host_id: int, user_id, red_id: int):

        red_cache_key = self.get_redis_key(red_id, column="grab_record")
        cache_column = "%s:%s" % (host_id, user_id)
        self.redis_cli.hset(red_cache_key, cache_column, time.strftime("%Y-%m-%d %H:%M:%S"))
        self.redis_cli.expire(red_cache_key, pay_config['red_envelope']['expiry_time'])

    """
    抢红包
    host_id 域id
    user_id 用户id
    red_id 抢红包id
    group_id 当前的群id
    """
    def grab(self, host_id: int, user_id, red_id: int, group_id):

        # 待抢的小红包队列
        lkey = self.get_redis_key(red_id, column="remain_queue")
        log_prefer = "grab:red_id:%s,host_id:%s,user_id:%s,action:" % (red_id, host_id, user_id)

        self.write_info_log(log_prefer+"open:begin")

        """
        拆过红包
        """
        if self.check_is_grab(host_id, user_id, red_id):
            self.write_info_log(log_prefer + "open:已经抢过:4006")
            return self.return_result(**{"ret": 0,
                                         "data": {"id": red_id},
                                         "error_code": 4006,
                                         "error_msg": self.error_code["4006"],
                                         "sql_error": ""})

        # 取出未抢小红包队列
        srid = self.redis_cli.lpop(lkey)
        if not srid:
            self.write_info_log(log_prefer + "open:红包已抢光:4007")
            # 红包已抢光
            return self.return_result(**{"ret": 0,
                                         "data": {"id": red_id},
                                         "error_code": 4007,
                                         "error_msg": self.error_code["4007"],
                                         "sql_error": ""})

        # 更新小红包记录 返回id ,以及领取的金额
        sql = """update public.red_envelope_draw_record set
                     host_id = %(host_id)s , user_id = %(user_id)s , draw_time=now()
                 where id = %(srid)s and  red_envelope_id = %(red_envelope_id)s and user_id is null
                 RETURNING id,credit
                 """
        # 更新红包余额， 以及领取数
        re_sql = """ update public.red_envelope re 
                         set draw_number = dr.draw_number ,balance = dr.balance 
                        from (select 
                            sum(case when (user_id is not null)  then 1 else 0 end) as draw_number,
                            sum(case when (user_id is null) then credit else 0.0 end) as balance
                            from public.red_envelope_draw_record
                            where red_envelope_id=%(red_envelope_id)s
                          )as dr
                         where re.id = %(red_envelope_id)s
                """

        # 更新红包余额， 以及领取数

        pg_cursor = self._rels.get_pg_dict_cursor()
        pg_cursor.execute('begin')

        try:

            pg_cursor.execute(sql, {"host_id": host_id, "user_id": user_id, "srid": srid, 'red_envelope_id': red_id})
            draw_record_row = pg_cursor.fetchone()
            # 判断 是否更新成功
            if not draw_record_row or str(draw_record_row['id']) != str(srid):
                # 没有更新，还原小红包，提示报错
                pg_cursor.execute("rollback")

                self.write_info_log(log_prefer + ("open:更新数据库失败:4003，1恢复小红包队列id:%s" % srid))
                self.redis_cli.rpush(lkey, srid)
                return self.return_result(**{"ret": 0,
                                             "data": {"id": red_id},
                                             "error_code": 4003,
                                             "error_msg": "服务器开小差啦…",
                                             "sql_error": ""})

            draw_record_row['credit'] = float(draw_record_row['credit'])

            pg_cursor.execute(re_sql, {'red_envelope_id': red_id})

            if 0 == parse_psycopg2_statusmessage(pg_cursor.statusmessage):
                # 没有更新，还原小红包，提示报错
                pg_cursor.execute("rollback")
                self.write_info_log(log_prefer + ("open:更新数据库失败:4003，2恢复小红包队列id:%s" % srid))
                self.redis_cli.rpush(lkey, srid)
                return self.return_result(**{"ret": 0,
                                             "data": {"id": red_id},
                                             "error_code": 4003,
                                             "error_msg": "服务器开小差啦……",
                                             "sql_error": ""})
            # 主动提交事务
            pg_cursor.execute("commit")
            pg_cursor.close()

            # 加入已抢红包的的列表
            self.set_grab_cache(host_id=host_id, user_id=user_id, red_id=red_id)
            # 更新红包缓存 只更新info表
            self.cache_red_info(red_id=red_id,only_info=True)
            # 加入红包发消息队列
            params = {"msg_type": "open_success", "id": srid, "group_id": group_id}
            self.add_qtalk_message_queue(**params)

            return self.return_result(**{"ret": 1,
                                         "data": {"id": red_id, "srid": int(srid), "credit": draw_record_row['credit']},
                                         "error_code": 200,
                                         "error_msg": "拆红包成功",
                                         "sql_error": ""})
        except Exception as e:
            pg_cursor.execute("rollback")
            pg_cursor.close()
            # 没有更新，还原小红包，提示报错
            self.write_info_log(log_prefer + ("open:数据库操作失败:4003，3恢复小红包队列id:%s" % srid))
            self.redis_cli.rpush(lkey, srid)
            return self.return_result(**{"ret": 0,
                                         "data": {"id": red_id, "srid": int(srid)},
                                         "error_code": 4003,
                                         "error_msg": "服务器开小差啦~",
                                         "sql_error": traceback.format_exc()})

    """
    获取红包qtalk 消息队列 redis key 
    """
    def get_qtalk_message_queue_redis_key(self):
        return self.get_redis_key(red_id="qtalk_message_queue")


    """
    红包 填加一条qtalk 消息列表
    msg_type = open_success| pay_success
    id  open_success? red_envelope_draw_record.id 
        pay_success ? red_envelope.id
    group_id 接收方所在的群或用户
    params  = {"group_id": "abcdefff", "id": "5", "msg_type": "open_success"}
    add_qtalk_message_queue(**params)
    """
    def add_qtalk_message_queue(self, **kwargs):
        queue_key = self.get_qtalk_message_queue_redis_key()
        self.redis_cli.rpush(queue_key, json.dumps(kwargs, ensure_ascii=False))

    """
    获取单独抢红包记录
    """
    def get_draw_record_info(self, srid: int):
        sql = """select redr.*,hu.user_name ,hi.host
                            from public.red_envelope_draw_record as redr
                            join public.host_info as hi on hi.id = redr.host_id
                            left join public.host_users as hu on redr.host_id = hu.host_id and redr.user_id = hu.user_id
                         where redr.id = %(id)s order by draw_time desc 
                        """

        pg_cursor = self._rels.get_pg_dict_cursor()

        pg_cursor.execute(sql, {'id': srid})

        row = pg_cursor.fetchone()
        pg_cursor.close()
        if row is None:
            return None

        draw_record = {
            'id': int(row['id']),  # id
            'host': str(row['host']),  # 抢的人域，主要用于发消息
            'host_id': int(row['host_id']),  # 抢的人所在的域
            'user_id': str(row['user_id']),  # 抢的人用户id
            'red_envelope_id': int(row['red_envelope_id']),  # 红包id
            'user_name': str(row['user_name']),  # 抢的人姓名
            'user_img': str(row['user_img']),  # 抢红包的头像
            'credit': decimal_2_float(row['credit'], 2),  # 抢的金额
            'has_transfer': int(row['has_transfer']),  # 是否已转帐
            'draw_time': row['draw_time'].strftime("%Y-%m-%d %H:%M:%S"),  # 抢的时间
        }
        return draw_record

    """
    获取红包已抢列表
    """
    def get_draw_record_list(self, red_id: int):

        sql = """select redr.*,redr.user_id || '@' || hi.host as host_user_id,hu.user_name 
                    ,RANK() OVER (ORDER BY credit DESC,redr.id asc ) as rank
                    ,max(draw_time) over() as last_draw_time
                    from public.red_envelope_draw_record as redr
                    join public.host_info as hi on hi.id = redr.host_id
                    left join public.host_users as hu on redr.host_id = hu.host_id and redr.user_id = hu.user_id
                 where redr.red_envelope_id = %(red_envelope_id)s and redr.user_id is not null order by draw_time desc 
                """

        pg_cursor = self._rels.get_pg_dict_cursor()

        pg_cursor.execute(sql, {'red_envelope_id': red_id})

        draw_record = []
        while True:
            row = pg_cursor.fetchone()
            if row is None:
                break

            draw_record.append({
                'id': int(row['id']),  # id
                'rank': 1 if int(row['rank']) == 1 else 0,  # 是否最佳
                'user_id': str(row['user_id']),  # 抢的人用户id
                'host_user_id': str(row['host_user_id']),  # 抢的人用户id
                'user_name': str(row['user_name']),  # 抢的人姓名
                'credit': decimal_2_float(row['credit'], 2),  # 抢的金额
                'has_transfer': int(row['has_transfer']),  # 是否已转帐
                'last_draw_time': row['last_draw_time'].strftime("%Y-%m-%d %H:%M:%S"),  # 最后抢的时间
                'draw_time': row['draw_time'].strftime("%Y-%m-%d %H:%M:%S"),  # 抢的时间
            })
        pg_cursor.close()

        return draw_record

