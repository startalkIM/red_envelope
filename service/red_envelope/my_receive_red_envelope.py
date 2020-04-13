#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
/red_envelope/my_receive
我发出去的红包
get_count 是否获取汇总信息 默认0 1为获取
"""
import time

from service.red_envelope.common import *
from service.red_envelope.common_sql import RedEnvelopeSql

my_receive_red_envelope_blueprint = Blueprint('my_receive_red_envelope', __name__)


@my_receive_red_envelope_blueprint.route('/my_receive')
@authorization
def current(user_id=None):
    json_dict = {"ret": 0, "message": "", "error_code": 0, "error_ext": "",  "data": {'list': [], 'count': {}}}
    # rels.host_id
    rels = RedEnvelopeSql()

    current_params = {
        # 当前页数
        "page": 1,
        # 每页显示数
        "pagesize": 5,
        # 要获取的年份
        "year": time.strftime("%Y"),
        # 是否获取汇总
        "get_count": 0
    }
    # 获取本页面必要参数
    current_params = get_request_need_args(**current_params)
    current_params['page'] = int(current_params['page'])
    current_params['pagesize'] = int(current_params['pagesize'])
    current_params['year'] = int(current_params['year'])
    current_params['get_count'] = int(current_params['get_count'])

    if current_params['page'] == 0:
        current_params['page'] = 1

    offset = (current_params['page'] - 1)*current_params['pagesize']

    sql_where = {
                 'user_id': user_id,
                 'year': current_params['year'],
                 'next_year': current_params['year']+1,
                 'offset': offset,
                 'pagesize': current_params['pagesize']
                 }

    if current_params['get_count']:
        json_dict['data']['count'] = rels.get_my_receive_red_envelope_count(sql_where)

    json_dict['data']['list'] = rels.get_my_receive_red_envelope(sql_where)
    json_dict['ret'] = 1
    json_dict['error_code'] = 200
    return display_json(json_dict)
