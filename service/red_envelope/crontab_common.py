#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
定义定时脚本相关函数
定时同时只允许存在一个，crontab_run_once
"""
import os
import psutil
import hashlib
import tempfile


class RedEnvCrontab:

    """
    获取琳时文件
    """

    @staticmethod
    def get_file(mark_file):
        return tempfile.gettempdir() .replace("\\", "/") + "/crontab_red_envelope_" + hashlib.md5(mark_file.encode("utf8")).hexdigest()

    """
    crontab 执行时 判断是否正在执行
    """
    @staticmethod
    def crontab_run_begin(mark_file):
        if mark_file is None:
            return False

        old_pid = RedEnvCrontab._read(mark_file)
        print("旧进程pid:%s" % old_pid)
        try:
            old_process = psutil.Process(int(old_pid))
        except Exception as e:
            error = str(e)
            old_process = ""
        print("旧进程信息%s" % old_process)
        if old_pid and int(old_pid) in psutil.pids():
            return True

        RedEnvCrontab._write(mark_file, str(os.getpid()))

        return False

    """
    crontab 执行完毕时将标志pid置空
    """
    @staticmethod
    def crontab_run_done(mark_file):
        RedEnvCrontab._write(mark_file, "-1")

    """
    写操作
    """
    @staticmethod
    def _write(mark_file, pid):
        if mark_file is None:
            return False
        file = RedEnvCrontab.get_file(mark_file)
        with open(file, 'w') as f:
            f.write(str(pid))
    """
    读操作
    """
    @staticmethod
    def _read(mark_file):
        file = RedEnvCrontab.get_file(mark_file)
        old_pid = None
        try:
            with open(file, 'r+') as f:
                old_pid = f.readline()
        except Exception as e:
            if str(e).find("No such file or directory") > 0:
                old_pid = None

        return old_pid
