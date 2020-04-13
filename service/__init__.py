# -*- encoding: utf8 -*-

__author__ = 'jingyu.he'
from flask import Flask, render_template
from service.red_envelope.bind_alipay_account import bind_alipay_account_blueprint
from service.red_envelope.get_bind_pay_account import get_bind_pay_account_blueprint
from service.red_envelope.create_red_envelope import create_red_envelope_blueprint
from service.red_envelope.open_red_envelope import open_red_envelope_blueprint
from service.red_envelope.grab_red_envelope import grab_red_envelope_blueprint
from service.red_envelope.get_red_envelope import get_red_envelope_blueprint
from service.red_envelope.pay_success import pay_success_blueprint
from service.red_envelope.oauth import alipay_oauth_blueprint
from service.red_envelope.my_send_red_envelope import my_send_red_envelope_blueprint
from service.red_envelope.my_receive_red_envelope import my_receive_red_envelope_blueprint
from service.red_envelope.alipay_app_login import alipay_app_login_blueprint
from service.all_average.create_aa import create_all_average_blueprint
from service.all_average.grab_all_average import grab_all_average_blueprint
from service.all_average.get_aa import get_all_average_blueprint

app = Flask(__name__, template_folder='../templates', static_folder='../static', static_url_path='/py/static')

#app.register_blueprint(parser_blueprint, url_prefix='/')
# app.register_blueprint(test_blueprint, url_prefix='/red_envelope')
app.register_blueprint(bind_alipay_account_blueprint, url_prefix='/red_envelope')
app.register_blueprint(get_bind_pay_account_blueprint, url_prefix='/red_envelope')
app.register_blueprint(create_red_envelope_blueprint, url_prefix='/red_envelope')
app.register_blueprint(open_red_envelope_blueprint, url_prefix='/red_envelope')
app.register_blueprint(grab_red_envelope_blueprint, url_prefix='/red_envelope')
app.register_blueprint(get_red_envelope_blueprint, url_prefix='/red_envelope')
app.register_blueprint(pay_success_blueprint, url_prefix='/red_envelope')
app.register_blueprint(alipay_oauth_blueprint, url_prefix='/red_envelope')
app.register_blueprint(my_send_red_envelope_blueprint, url_prefix='/red_envelope')
app.register_blueprint(my_receive_red_envelope_blueprint, url_prefix='/red_envelope')
app.register_blueprint(alipay_app_login_blueprint, url_prefix='/red_envelope')
app.register_blueprint(create_all_average_blueprint, url_prefix='/all_average')
app.register_blueprint(grab_all_average_blueprint, url_prefix='/all_average')
app.register_blueprint(get_all_average_blueprint, url_prefix='/all_average')




@app.route('/healthcheck.html', methods=['GET'])
def healthcheck():
    return 'ok'
#def healthcheck():
#    return render_template('healthcheck.html')
