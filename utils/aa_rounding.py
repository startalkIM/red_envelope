#!/usr/bin/env python
# -*- coding:utf-8 -*-

import logging


def cal_avg_credit(num: int, credit: float):
    if num <= 0:
        logging.info("aa收款个数小于1")
        return False
    if credit < 0.01:
        logging.info("收款金额小于1分")
        return False
    avg_credit = float("%.2f" % (credit / num))
    if avg_credit < credit / num:
        avg_credit += 0.01
        logging.info("人均收款 {} 元".format(avg_credit))
    return avg_credit


