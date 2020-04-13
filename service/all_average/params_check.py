#!/usr/bin/env python
# -*- coding:utf-8 -*-

from utils.aa_rounding import *

"""
获取参数：
    action - create_all_average
    group_id - group@conference.domain
    user_id - user@domain
    credit - 总额 (%.2f 元)
    number - 份数
    detail - {"usera":money (%.2f), "userb":money (%.2f)}
    atype - 指定数额的custom 平分的normal
    content - 备注
"""

"""
检查金额
"""


def check_detail(params: dict):
    paid_type = params.get("atype")
    number = params.get("number")
    try:
        credit = float(params.get("credit"))
    except Exception as e:
        print("credit float失败")
        return False

    details = params.get("detail")
    # current = 0.00

    if not isinstance(details, dict):
        logging.warning("明细类型错误")
        return False

    # normal情况下由服务器计算每人的金额
    # for money in details.values():
    #     if not isinstance(money, float):
    #         logging.warning("金额非浮点数")
    #         return False
    #     if money <= 0.01:
    #         return False
    #     current += money
    # 检查总金额和人数
    # if current != credit:
    #     logging.warning("总金额不匹配")
    #     return False
    if len(details.keys()) != int(number):
        logging.warning("人数不匹配")
        return False
    if paid_type == "normal":
        # if (current / number) != cal_avg_credit(num=number, credit=credit):  # TODO 需要和客户端确定四舍五入的金额算法
        #     logging.warning("金额计算错误")
        #     return False
        return True
    elif paid_type == "custom":
        pass
    else:
        logging.warning("aa类型错误")
        return False


def check_params(params):
    result = {"ret": 0, "err_msg": "", "err_ext": ""}
    """检查action"""
    if params.get("action") != "create_all_average":
        result["err_msg"] = "wrong action"
        return result
    """检查金额类型"""
    number = params.get("number")
    try:
        number = int(number)
    except Exception as e:
        print(e)
        result["err_msg"] = "wrong number"
        return result


    """检查user_id 以及 """
    user_id = params.get("user_id")
    group_id = params.get("group_id")
    detail = params.get("detail")
    if not user_id or not group_id or not detail:
        result["err_msg"] = "wrong params"
        result["err_ext"] = "缺少用户和或群组"
        return result
    if not check_detail(params):
        result["err_msg"] = "wrong detail"
        return result
    result["ret"] = 1
    return result
