#!/usr/bin/env python
# -*- coding:utf-8 -*-

from service.red_envelope.common import *
from service.all_average.common_sql import AllAverageSql

get_all_average_blueprint = Blueprint('get_all_average', __name__)

"""
{
  "data": {
    "user_status": 0, # 0 未支付 1 已支付 2 无关
    "paid_money": 0.03, # 需付款金额
    "need_paid":0.00,
    "create_time": "2019-06-14 14:34:15", #aa创建时间
    "total": 0.06, # aa总金额
    "paid_number": 1, # 已抢的个数 , 包含发起者本身
    "unpaid_number": 1, # 已抢的个数
    "payer_record": [ #aa支付人信息
    {
      "credit": 0.03, #抢的金额
      "has_transfer": 1, # 是否已转帐
      "user_id": "suozhu.li", # 抢的人
      "user_img": "/file/v2/download/avatar/d1334fe77c114d21552ac8501db6f057.gif", # 抢的人的头像
      "user_name": "李锁柱" #抢的真实姓名
    },
    {
      "credit": 0.03, #抢的金额
      "has_transfer": 0, # 是否已转帐
      "user_id": "jingyu.he", # 抢的人
      "user_img": "/file/v2/download/avatar/d1334fe77c114d21552ac8501db6f057.gif", # 抢的人的头像
      "user_name": "何靖宇" #抢的真实姓名
    }],
    "aa_content": "测试的", # aa内容 
    "aa_number": 2, # aa个数
    "aa_type": "normal", # aa类型  normal | customized
    "payee_id": "suozhu.li", # 发红包的人
    "payee_img": "/file/v2/download/avatar/d1334fe77c114d21552ac8501db6f057.gif", # 头像
    "payee_name": "李锁柱" # 发红包的真实姓名
  },
  "error_code": 0,
  "error_ext": "",
  "message": "获取成功",
  "ret": 1
}
"""

@get_all_average_blueprint.route('/getaa', methods=['POST'])
@authorization
def get_aa(user_id: str = None):
    json_dict = {
        "ret": 0, "message": "", "error_code": 0, "error_ext": "", "data": {}
    }
    current_params = {
        # 公共参数
        "user_id": "",
        # 必要参数
        "aid": 0
    }
    current_params = get_request_need_args(**current_params)
    user_id = current_params['user_id']
    aid = current_params['aid']
    aas = AllAverageSql()


    # """ 检查aa是否存在 以及用户是否有权限查看 """
    # check_ret = aas.check_user(aid, user_id)
    # if not check_ret['ret']:
    #     json_dict['message'] = check_ret['error_message']
    #     return json_dict

    """获取aa的发起人， 发起时间， 总金额， 收到金额，已支付人数和金额， 微支付人数和金额"""
    sql_ret = aas.get_aa_detail(aid=aid, user_id=user_id)
    if not sql_ret['ret']:
        print(sql_ret['error_message'])
        json_dict['message'] = sql_ret['error_message']
    json_dict['ret'] = 1
    json_dict['message'] = '获取aa成功'
    json_dict['data'] = sql_ret['data']
    print("{}".format(json_dict))
    return jsonify(json_dict)
