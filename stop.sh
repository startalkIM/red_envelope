#!/usr/bin/env bash

cd /startalk/red_envelope
source /startalk/qtalk_search/venv/bin/activate
supervisorctl -c /startalk/qtalk_search/conf/supervisor.conf stop red_envelope