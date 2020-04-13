#!/usr/bin/env python
# -*- coding:utf-8 -*-

from service.all_average.common_sql import AllAverageSql

"""
每个aa过期时间暂定
每个aa的最大收款金额暂定， 默认为99999
aa的支付节点为1天后提醒收款者未收齐
"""


class AllAverage:
    # 错误码
    error_code = {
        "4001": "id的格式错误",
        "4002": "aa不存在",
        "4003": "数据库执行失败",
        "4004": "缓存失败",
        "4005": "aa已过期",
        # "4006": "你已领取该红包",
        # "4007": "红包已抢光",
        "4008": "未登录",
        "4009": "参数出错",
        "4010": "aa金额错误",  # 例如超过99999
        "4011": "订单aa已存在",
        "4021": "鉴权失败",
        "4022": "非法访问",
        "4023": "不支持的支付方式",
        # "4030": "今日抢同一发送用户红包超限",
        "4300": "用户未绑定支付宝",
    }

    def __init__(self, **params):
        self.id = None  # aa的id
        self._aas = AllAverageSql()
        self._table_fields = ["id", "host_id", "user_id", "aa_type", "credit", "balance", "red_number", "draw_number",
                              "red_content", "order_id", "expire_time", "group_chat_id", "create_time", "update_time"]

        self.redis_cli = self._aas.get_redis_conn()
        names = self.__dict__
        for k in self._table_fields:
            names[k] = ""

        # 必须是个字典
        if not isinstance(params, dict):
            # 传参错误
            self.write_info_log("红包id%s:4009：%s" % (str(params['id']), str(self.error_code['4009'])))
            raise Exception('4009')

        names = self.__dict__
        for k in names:
            if k in params.keys():
                names[k] = params[k]

    """写日志"""

    def write_info_log(self, message):
        self._aas.write_info_log(log_type="all_average", message=message)

    """
    创建一条新的aa
    1.插入一条
    """

    def create(self):
        """
        $1 user_id ( jingyu.he@ejabhost1 )
        $2 members ( json.dumps({'binz.zhang':12.00}) )
        $3 aa_type ( 'customize' \ 'normal' )
        $4 credit ( 12.00 )
        $5 aa_number
        :return:
        """
        self.write_info_log("AAid {} 创建初始化".format(self.id))
        if len(str(self.id)) > 0 and str(self.id) != "0":
            # 红包已经存在
            return self.return_result(**{"ret": 0,
                                         "data": {"id": self.id},
                                         "error_code": 4011,
                                         "error_msg": self.error_code['4011'],
                                         "sql_error": ""})
        sql = """ INSERT INTO public.all_average(host_id, organizer, members, aa_type, credit, aa_number, aa_content, order_id, expire_time, group_chat_id, status) SELECT  {self_id}, 'jingyu.he@ejabhost', '{"binz.zhang@ejabhost1": 12.00}', 'customize', 12.00, 1, '', 1, {expire_time}}, 'aaa@conference.ejabhost', 0""".format(
            self_id=self.id, expire_time=self.expire_time)

    """
    获取一条aa的状态，包括每个人待支付人的姓名、头像、金额、支付状态、
    aa的总金额、 已收金额、 title
    aa的支付人数
    aa的创建日期
    """

    def get_info(self):
        pass

    """
    创建每个待支付者的数据 并且插入redis"""

    def generate_sub_paid(self):
        pass
