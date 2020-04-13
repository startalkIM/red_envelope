#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'jingyu.he'

import logging
import logging.config
import logging.handlers
from utils.get_conf import get_config_file, get_logger_file

config = get_config_file()
level = config['log']['level'].lower()
router = {
    'critical': logging.CRITICAL,
    'fatal': logging.FATAL,
    'error': logging.ERROR,
    'warning': logging.WARNING,
    'warn': logging.WARN,
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'notset': logging.NOTSET
}
log_level = router.get(level, logging.INFO)
log_root = get_logger_file()
logger_register = {
    'root': '',
    'search': '',
    'sharemsg': '',
    'meetingdetail': '',
    'updatecheck': '',
    'cache': '',
    'sql': '',
    'error': '',
    'test': '',
    'read_envelope_check_ck': '',
    'alipay': '',
    'red_envelope': '',
    'red_envelope_transfer': '',
    'red_envelope_refund': '',
    'red_envelope_qtalkmessage': '',
    'order_list': '',
    'order_trace': '',
    'pay_success': '',
    'all_average': '',
    'all_average_transfer': '',
    'all_average_qtalkmessage': '',
}
for _k, _v in logger_register.items():
    logger_register[_k] = log_root + _k + '.log'


def configure_logger(name, log_path=''):
    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'default': {'format': '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s - %(message)s',
                        'datefmt': '%Y-%m-%d %H:%M:%S'},
            'normal': {'format': '%(asctime)s - %(levelname)s - %(message)s',
                       'datefmt': '%Y-%m-%d %H:%M:%S'}
        },
        'handlers': {
            'console': {
                'level': log_level,
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'stream': 'ext://sys.stdout'
            },
            'root': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['root'],
                'encoding': 'utf-8',
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 3
            },
            'error': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['error'],
                'encoding': 'utf-8',
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 3
            },
            'search': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['search'],
                'encoding': 'utf-8',
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 3
            },
            'sharemsg': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['sharemsg'],
                'encoding': 'utf-8',
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 3
            },
            'meetingdetail': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['meetingdetail'],
                'encoding': 'utf-8',
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 3
            },
            'updatecheck': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['updatecheck'],
                'encoding': 'utf-8',
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 3
            },
            'cache': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['cache'],
                'encoding': 'utf-8',
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 3
            },
            'sql': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['sql'],
                'encoding': 'utf-8',
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 3
            },
            'test': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['test'],
                'encoding': 'utf-8',
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 3
            },
            'read_envelope_check_ck': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['read_envelope_check_ck'],
                'encoding': 'utf-8',
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 3
            },
            'alipay': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['alipay'],
                'encoding': 'utf-8',
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 3
            },
            'red_envelope': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['red_envelope'],
                'encoding': 'utf-8',
                'maxBytes': 100 * 1024 * 1024,
                'backupCount': 5
            },
            'red_envelope_transfer': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['red_envelope_transfer'],
                'encoding': 'utf-8',
                'maxBytes': 100 * 1024 * 1024,
                'backupCount': 5
            },
            'red_envelope_refund': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['red_envelope_refund'],
                'encoding': 'utf-8',
                'maxBytes': 100 * 1024 * 1024,
                'backupCount': 5
            },
            'red_envelope_qtalkmessage': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['red_envelope_qtalkmessage'],
                'encoding': 'utf-8',
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 5
            },
            'all_average': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['all_average'],
                'encoding': 'utf-8',
                'maxBytes': 100 * 1024 * 1024,
                'backupCount': 5
            },
            'all_average_transfer': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['all_average_transfer'],
                'encoding': 'utf-8',
                'maxBytes': 100 * 1024 * 1024,
                'backupCount': 5
            },
            'all_average_qtalkmessage': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['all_average_qtalkmessage'],
                'encoding': 'utf-8',
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 5
            },
            'order_list': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['order_list'],
                'encoding': 'utf-8',
                'maxBytes': 100 * 1024 * 1024,
                'backupCount': 5
            },
            'order_trace': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['order_trace'],
                'encoding': 'utf-8',
                'maxBytes': 100 * 1024 * 1024,
                'backupCount': 5
            },
            'pay_success': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': logger_register['pay_success'],
                'encoding': 'utf-8',
                'maxBytes': 100 * 1024 * 1024,
                'backupCount': 5
            },
        },
        'loggers': {
            'root': {
                'level': log_level,
                'handlers': ['console', 'root', 'error']
            },
            'search': {
                'level': log_level,
                'handlers': ['console', 'search', 'error']
            },
            'sharemsg': {
                'level': log_level,
                'handlers': ['console', 'sharemsg', 'error']
            },
            'meetingdetail': {
                'level': log_level,
                'handlers': ['console', 'meetingdetail', 'error']
            },
            'updatecheck': {
                'level': log_level,
                'handlers': ['console', 'updatecheck', 'error']

            },
            'cache': {
                'level': log_level,
                'handlers': ['console', 'cache', 'error']
            },
            'sql': {
                'level': log_level,
                'handlers': ['console', 'sql', 'error']
            },
            'test': {
                'level': log_level,
                'handlers': ['console', 'test', 'error']
            },
            'read_envelope_check_ck': {
                'level': log_level,
                'handlers': ['console', 'read_envelope_check_ck', 'error']
            },
            'alipay': {
                'level': log_level,
                'handlers': ['console', 'alipay', 'error']
            },
            'red_envelope': {
                'level': log_level,
                'handlers': ['console', 'red_envelope', 'error']
            },
            'red_envelope_transfer': {
                'level': log_level,
                'handlers': ['console', 'red_envelope_transfer', 'error']
            },
            'red_envelope_refund': {
                'level': log_level,
                'handlers': ['console', 'red_envelope_refund', 'error']
            },
            'red_envelope_qtalkmessage': {
                'level': log_level,
                'handlers': ['console', 'red_envelope_qtalkmessage', 'error']
            },
            'all_average': {
                'level': log_level,
                'handlers': ['console', 'red_envelope', 'error']
            },
            'all_average_transfer': {
                'level': log_level,
                'handlers': ['console', 'red_envelope_transfer', 'error']
            },
            'all_average_qtalkmessage': {
                'level': log_level,
                'handlers': ['console', 'red_envelope_qtalkmessage', 'error']
            },
            'order_list': {
                'level': log_level,
                'handlers': ['console', 'order_list', 'error']
            },
            'order_trace': {
                'level': log_level,
                'handlers': ['console', 'order_trace', 'error']
            },
            'pay_success': {
                'level': log_level,
                'handlers': ['console', 'pay_success', 'error']
            }

        },
        'disable_existing_loggers': False
    })
    return logging.getLogger(name)

