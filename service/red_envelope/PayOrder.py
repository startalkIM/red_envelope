#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
支付订单相关操作
"""

import time
import traceback
from flask import Blueprint,  Response, json, request, jsonify
from service.red_envelope.common import authorization, display_json, get_request_need_args, validate_mobile, validate_email, decimal_2_float, parse_psycopg2_statusmessage

from service.red_envelope.common_sql import RedEnvelopeSql

"""
test 
po = PayOrder({"order_type": "red_envelope", "credit": 10.02, "pay_channel": "alipay", "order_comments":{"a":1, "c": 10.2, "e":"中国人 民"}})
f = po.create()
"""


class PayOrder:
    error_code = {
        "2001": "订单不存在",
        "2002": "该AA收款订单已存在，请到我的账单里查看",
        "2003": "未找到用户手机号信息",
        "2004": "order表插入失败",
        "2005": "该订单不能进行取消操作",
        "2006": "数据库操作失败",
        "2007": "初始化参数错误",
        "2008": "合并订单至少为2个订单",
        "2009": "合并的订单非订单类实例",
        "2010": "订单不是未支付状态,不能进行合单支付",
        "2011": "不是一个活动的订单不能进行合单支付",
        "2012": "不同类型的订单不能进行合单支付",
        "2013": "不同帐号的订单不能进行合单支付",
        "2100": "支付帐号发生问题",
        "2101": "支付成功后重复回调",
        "2102": "订单已支付",
        "2103": "订单金额出现问题",
        "2104": "订单不能退款",
        "2105": "订单金额超过限额",
        "2106": "不是合单支付不能进行合单退款",
        "2201": "子订单由父订单更新订单状态"
    }
    """
    order_type red_envelope=发红包,return_balance=退款,aa=AA
    pay_channel
    pay_account 支付的帐户 可传可不传， 红包打款需要用到 payee_login_id
    """
    def __init__(self, **params):
        self._rels = RedEnvelopeSql()
        # order_list 表的相关字段
        self._table_fields = ["id", "order_type", "pay_channel", "pay_account", "credit", "remain_credit",
                              "refund_credit", "order_no", "order_line", "refund_order_line", "pay_order_no",
                              "pay_order_line", "state", "order_comments", "create_time", "pay_time",
                              "cancel_time", "refund_time", "aid"]
        # 初始化 将本地的字段 置空
        self.aid = None
        names = self.__dict__
        for k in self._table_fields:
            if k in params.keys():
                names[k] = params[k]
            else:
                names[k] = ""
        # 订单初始化必须剩余金额一至
        names['remain_credit'] = names['credit']
        if str(self.state) == "":
            self.state = "unpay"
        # 处理id 预处理变量 放最后处理， 会覆盖变量
        if "id" in params.keys():
            if type(params['id']) is not int or params['id'] <= 0:
                # id的格式错误
                self.write_info_log("订单id%s:2001：%s" % (str(params['id']), str(self.error_code['2001'])))
                raise Exception("2001")
            self.write_info_log("订单id%s:初始化" % str(params['id']))
            info = self.get_order_info(order_id=params['id'])

            if 'id' not in info.keys() or str(info['id']) != str(params['id']):
                # 订单不存在
                self.write_info_log("订单id%s:2001：%s" % (str(params['id']), self.error_code['2001']))
                raise Exception("2001")
            # 重写 所有的变量值
            names = self.__dict__
            for k in info:
                names[k] = info[k]

            self.write_info_log("订单id%s:所有订单信息:%s" % (str(params['id']), json.dumps(info, ensure_ascii=False)))

    """
    获取当日 用户所有发出的红包额度
    """

    def get_user_today_pay_red_envelope(self, pay_channel=None, pay_account=None):

        if pay_channel is None:
            pay_channel = self.pay_channel
            pay_account = self.pay_account
        pg_cursor = self._rels.get_pg_dict_cursor()

        sql = """SELECT  coalesce(sum(credit),0.0) as sum FROM public.order_list 
                    where pay_channel =%(pay_channel)s and  pay_account = %(pay_account)s
                    and state = 'pay'  and  order_type = 'red_envelope'  and pay_time::date = current_date
               """
        self.write_info_log("sql:" + sql)
        try:
            pg_cursor.execute(sql, {'pay_channel': pay_channel, 'pay_account': pay_account})
            row = pg_cursor.fetchone()
        except Exception as e:
            row = None
            sql_error = str(pg_cursor.query) + " error: " + str(e) + ",trace:" + traceback.format_exc()
            self.return_result(**{"ret": 0,
                                  "data": {"id": self.id},
                                  "error_code": 4003,
                                  "id": 0,
                                  "error_msg": "数据库执行失败",
                                  "sql_error": sql_error})
        pg_cursor.close()
        return float(row['sum'])

    """
    根据id获取一条订单信息
    """
    def get_order_info(self, order_id):
        pg_cursor = self._rels.get_pg_dict_cursor()
        sql = "select * from public.order_list where id=%(id)s"

        try:
            pg_cursor.execute(sql, {'id': int(order_id)})
            row = pg_cursor.fetchone()
        except Exception as e:
            row = None
            sql_error = str(pg_cursor.query) + " error: " + str(e) + ",trace:" + traceback.format_exc()
            self.return_result(**{"ret": 0,
                                  "data": {"id": self.id},
                                  "error_code": 4003,
                                  "id": 0,
                                  "error_msg": "数据库执行失败",
                                  "sql_error": sql_error})
        pg_cursor.close()

        info = {}
        for k in self._table_fields:
            info[k] = ""
        if row is not None:
            for k in info:
                if k in ['create_time', 'pay_time', 'cancel_time', 'refund_time']:
                    # timestamp 格式出来的是date time (Mon, 03 Jun 2019 11:02:24 GMT)需要转换一下格式用于显示
                    if row[k] is not None:
                        info[k] = row[k].strftime("%Y-%m-%d %H:%M:%S")
                elif k in ['credit', 'remain_credit', 'refund_credit']:
                    info[k] = float(row[k])
                else:
                    info[k] = row[k]

        return info

    """
    生成支付订单no
    """
    def generate_order_no(self):
        return "%s_%s_%s" % ("qt", str(time.strftime("%Y%m%d%H%M%S")), str(self.get_id()))
    """
    生成订单流水
    """
    def generate_order_line(self):
        return "%s_%s_%s" % ("qtl", str(time.strftime("%Y%m%d%H%M%S")), str(self.get_id()))

    """
    生成转帐的订单号
    qts_父订单id_子红包的draw_record_id_抢红包时间
    """

    def generate_sub_red_envelope_order_no(self, sub_red_envelope_id, draw_time_str):
        return "%s_%s_%s_%s" % ("qts", str(self.get_id()), str(sub_red_envelope_id), str(draw_time_str))

    """
        生成退款订单流水号 一个订单 只有一个流水号
    """

    def generate_refund_order_no(self, create_time_str):
        return "%s_%s_%s" % ("qtr", str(self.get_id()), str(create_time_str))

    """
    获取 order_list 表 自增id
    """

    def get_new_order_id(self):
        sql = "select nextval('order_list_id_seq'::regclass) as id"
        pg_cursor = self._rels.get_pg_dict_cursor()

        sql_error = ""
        try:
            pg_cursor.execute(sql)
            row = pg_cursor.fetchone()
        except Exception as e:
            row = None
            sql_error = str(pg_cursor.query) + " error: " + str(e) + ",trace:" + traceback.format_exc()
            self.return_result(**{"ret": 0,
                                  "data": {"id": self.id},
                                  "error_code": 4003,
                                  "error_msg": "数据库执行失败",
                                  "sql_error": sql_error})

        pg_cursor.close()
        return row['id'] if row is not None else 0

    def get_id(self):
        return self.id

    def get_credit(self):
        return self.credit

    def get_remain_credit(self):
        return self.remain_credit

    def get_refund_credit(self):
        return self.refund_credit

    def get_pay_time(self):
        return self.pay_time

    def get_order_type(self):
        return self.order_type

    def get_state(self):
        return self.state

    def get_order_no(self):
        return self.order_no

    def get_pay_channel(self):
        return self.pay_channel

    def get_pay_account(self):
        return self.pay_account

    def get_pay_order_no(self):
        return self.pay_order_no

    def get_pay_order_line(self):
        return self.pay_order_line

    """
    创建订单
    """
    def create(self):
        # 获取order表自增id
        order_id = self.get_new_order_id()

        self.write_info_log("订单id%s:创建订单开始:" % (order_id))

        if order_id <= 0:
            return self.return_result(**{"ret": 0,
                                         "data": {"id": 0},
                                         "error_code": 4003,
                                         "error_msg": "数据库执行失败",
                                         "sql_error": ""})
        self_id_tmp = self.id
        self.id = order_id

        order_no = self.generate_order_no()

        sql = """insert into public.order_list (id,order_type,pay_channel,pay_account,credit,remain_credit,order_no,state,order_comments)
                 values (%(id)s,%(order_type)s,%(pay_channel)s,%(pay_account)s,%(credit)s,%(remain_credit)s,%(order_no)s,%(state)s,%(order_comments)s)
              """
        params = {"id": order_id, "order_type": self.order_type, "pay_channel": self.pay_channel,
                  "pay_account": self.pay_account, "credit": self.credit, "remain_credit": self.credit, "order_no": order_no,
                  "state": self.state, "order_comments": self.order_comments
                  }


        self.write_info_log("订单id%s:获取参数:%s" % (order_id, json.dumps(params, ensure_ascii=False)))
        pg_cursor = self._rels.get_pg_dict_cursor()

        sql_error = ""
        # execute sql语句只要有错误 就会触发异常
        try:
            pg_cursor.execute(sql, params)
            if self.aid:
                sql = """UPDATE public.order_list SET aid = %(aid)s where id = %(order_id)s"""
                pg_cursor.execute(sql, {"aid":self.aid, "order_id":order_id})
            result = parse_psycopg2_statusmessage(pg_cursor.statusmessage)
            self.write_info_log("订单id%s:生成新订单成功" % order_id)
        except Exception as e:
            self.write_info_log("订单id%s:生成新语句,%s" % (order_id, str(pg_cursor.query)))
            result = str(e)
            sql_error = " error: " + result + ",trace:" + str(traceback.format_exc())
        pg_cursor.close()
        # 插入成功返回的是 INSERT 0 1
        # pg_cursor.query 是插入的sql 语句
        if str(result) == "1":
            self.order_no = str(order_no)
            return self.return_result(**{"ret": 1,
                                         "data": {"id": self.id},
                                         "error_code": 200,
                                         "error_msg": "",
                                         "sql_error": sql_error})
        else:
            self.id = self_id_tmp
            return self.return_result(**{"ret": 0,
                                         "data": {"id": 0},
                                         "error_code": 4003,
                                         "error_msg": "数据库执行失败",
                                         "sql_error": sql_error})

    """
    插入订单流水， 用于刚建红包时|红包打款，红包退款 等流水使用
    默认参数使用红包对应订单的，即建红包
    
    op 包含 pay|refund|return_balance
    """
    def insert_order_trace(self, **params):

        if type(params) is not dict:
            params = {}
        params['order_id'] = params['order_id'] if "order_id" in params.keys() else self.get_id()
        # 订单流水每次都 要生成新的, 回传的时候更新 流水状态
        params['order_line'] = params['order_line'] if "order_line" in params.keys() else self.generate_order_line()
        params['pay_channel'] = params['pay_channel'] if "pay_channel" in params.keys() else self.get_pay_channel()
        params['pay_account'] = params['pay_account'] if "pay_account" in params.keys() else self.get_pay_account()
        params['pay_status'] = params['pay_status'] if "pay_status" in params.keys() else self.get_state()
        params['credit'] = params['credit'] if "credit" in params.keys() else self.get_credit()
        params['pay_order_no'] = params['pay_order_no'] if "pay_order_no" in params.keys() else self.get_pay_order_no()
        params['pay_order_line'] = params['pay_order_line'] if "pay_order_line" in params.keys() else self.get_pay_order_line()

        params['op'] = str(params['op']) if "op" in params.keys() else "pay"
        params['trace_comments'] = params['trace_comments'] if "trace_comments" in params.keys() \
                                                               and type(params['trace_comments']) is dict else {}

        sql = "insert into public.order_trace ("

        # 插入 如果为空的 则会插入失败， 由其是pay_time 一些特殊字段
        for k in params:
            if params[k] is None:
                continue
            sql = sql + k + ","

        sql = sql.strip(",")
        sql = sql + ") values ("

        for k in params:
            if params[k] is None:
                continue
            sql = sql + "%(" + k + ")s,"
        sql = sql.strip(",")
        sql = sql + ")"

        print("插入订单失误 {}".format(params))
        self.write_info_log("订单id{}:插入订单流水:{}".format(self.id, json.dumps(params, ensure_ascii=False)))
        pg_cursor = self._rels.get_pg_dict_cursor()

        sql_error = ""
        # execute sql语句只要有错误 就会触发异常
        try:
            pg_cursor.execute(sql, params)
            result = parse_psycopg2_statusmessage(pg_cursor.statusmessage)
            self.write_info_log("订单id%s:生成订单流水成功" % self.id)
        except Exception as e:
            self.write_info_log("订单id%s:生成订单流水失败语句,%s" % (self.id, str(pg_cursor.query)))
            result = str(e)
            sql_error = " error: " + result + ",trace:" + str(traceback.format_exc())
        pg_cursor.close()
        # 插入成功返回的是 INSERT 0 1
        # pg_cursor.query 是插入的sql 语句
        if str(result) == "1":
            return self.return_result(**{"ret": 1,
                                         "data": {"order_line": params['order_line']},
                                         "error_code": 200,
                                         "error_msg": "",
                                         "sql_error": sql_error})
        else:
            return self.return_result(**{"ret": 0,
                                         "data": {"order_line": 0},
                                         "error_code": 4003,
                                         "error_msg": "数据库执行失败",
                                         "sql_error": sql_error})

    """
    根据流水号获取 order_trace 信息，只获取一条
    """
    def get_order_trace(self, order_line=None):
        if not order_line:
            return False

        sql = """select id, order_id, order_line, pay_channel, pay_account, pay_status, 
       pay_order_no, pay_order_line, credit, op, op_time, trace_comments FROM public.order_trace
                       where order_line=%(order_line)s"""

        pg_cursor = self._rels.get_pg_dict_cursor()
        try:
            pg_cursor.execute(sql, {'order_line': str(order_line)})
            row = pg_cursor.fetchone()
        except Exception as e:
            row = None
            sql_error = str(pg_cursor.query) + " error: " + str(e) + ",trace:" + traceback.format_exc()
            self.return_result(**{"ret": 0,
                                  "data": {"id": self.id},
                                  "error_code": 4003,
                                  "id": 0,
                                  "error_msg": "数据库执行失败",
                                  "sql_error": sql_error})
        pg_cursor.close()

        if row is None:
            return False

        info = {
            "id": row['id'],
            "order_id": row['order_id'],
            "order_line": row['order_line'],
            "pay_channel": row['pay_channel'],
            "pay_account": row['pay_account'],
            "pay_status": row['pay_status'],
            "pay_order_no": row['pay_order_no'],
            "pay_order_line": row['pay_order_line'],
            "credit": float(row['credit']),
            "op": row['op'],
            "op_time": row['op_time'].strftime("%Y-%m-%d %H:%M:%S"),
            "trace_comments": json.loads(row['trace_comments'])
        }

        return info

    """
    更新流水表支付状态，用于，支付回调， 红包打款，红包退款，打款回调，退款回调
    order_line 支付流水号
    trace_comments 可以是调用支付宝的倾向于部 dict 
    pay_order_no  支付订单号即支付宝的 auth_no
    pay_order_line 支付流水号 即支付宝的 operation_id
    pay_status unpay|pay|return_balance_ing|re_balance_ok|refund_ing|refund_ok
    """
    def update_order_trace(self, order_line, pay_status, pay_order_no, pay_order_line, trace_comments):

        sql = """UPDATE public.order_trace 
                        SET pay_status = %(pay_status)s, 
                        trace_comments = trace_comments || %(trace_comments)s ,
                        pay_order_line=%(pay_order_line)s, pay_order_no=%(pay_order_no)s
                        WHERE order_line = %(order_line)s 
                    """

        if not isinstance(trace_comments, dict):
            trace_comments = {}

        pg_cursor = self._rels.get_pg_dict_cursor()
        try:
            pg_cursor.execute(sql, {"order_line": order_line,
                                    "pay_status": pay_status,
                                    "trace_comments": trace_comments,
                                    "pay_order_no": pay_order_no,
                                    "pay_order_line": pay_order_line})
            result = parse_psycopg2_statusmessage(pg_cursor.statusmessage)
            self.write_info_log("order_line%s:更新订单流水成功" % order_line)
        except Exception as e:

            self.write_info_log("order_line%s:更新订单流水失败语句,%s,error:%s" % (self.id, str(pg_cursor.query), str(e)))

        pg_cursor.close()
        return True if str(result) == "1" else False

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
            self._rels.write_error_log(log_type="order_list",
                                       message="""ret:%s,data:%s,error_code:%s,error_msg:%s,sql_error:%s"""
                                               % (str(ret), str(data), str(error_code), str(error_msg), str(sql_error)))
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
        self._rels.write_info_log(log_type="order_list", message=message)
