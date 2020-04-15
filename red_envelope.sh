#!/usr/bin/env bash
cd /startalk/red_envelope
source /startalk/qtalk_search/venv/bin/activate
if [[ $1 == 'init' ]]; then
echo -e "\
[program:red_envelope]
command     = /startalk/qtalk_search/venv/bin/gunicorn -w6 start_service:app -b 0.0.0.0:5002
environment = PATH=\"/startalk/qtalk_search/venv/bin\",PYTHONPATH=\"/startalk/red_envelope:PYTHONPATH\"
directory   = service
startsecs   = 3

autostart=true
autorestart=true

redirect_stderr         = true
stdout_logfile_maxbytes = 50MB
stdout_logfile_backups  = 10
stdout_logfile          = /startalk/startalk_all_average/log/access.log" >> /startalk/qtalk_search/conf/supervisor.conf
fi
supervisorctl -c /startalk/qtalk_search/conf/supervisor.conf update
supervisorctl -c /startalk/qtalk_search/conf/supervisor.conf restart red_envelope

#ps aux | grep red_envelope/start_service.py | grep -v "grep" | awk -F' ' '{print $2}'| xargs -I {} sudo kill -9 {}
#nohup python -u /startalk/red_envelope/start_service.py ${env} &>/startalk/red_envelope/log/start_redenvelope.log &
