#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
支付宝类二次封装，主要回调验签、app支付、红包打款、红包退款、红包流水详细

收发现金红包 https://docs.open.alipay.com/301/
alipay 返回code https://docs.open.alipay.com/common/105806
异步通知验签 https://docs.open.alipay.com/291/106074
自行实现验签
https://docs.open.alipay.com/200/106120
qlipay 签名方法
https://docs.open.alipay.com/20190111144811460526/quickstart/
python sdk https://pypi.org/project/alipay-sdk-python/

自行实现签名
https://docs.open.alipay.com/291/106118

"""

import uuid
import datetime
import hashlib
import traceback
from conf.constants import *
from utils.logger_conf import configure_logger
from flask import json

# 支付宝相关的

from service.red_envelope.AlipayCertClientConfig import AlipayCertClientConfig
from service.red_envelope.AlipayCertClient import AlipayCertClient as DefaultAlipayClient

# 授权

from alipay.aop.api.domain.AlipayOpenAuthTokenAppModel import AlipayOpenAuthTokenAppModel
from alipay.aop.api.request.AlipayOpenAuthTokenAppRequest import AlipayOpenAuthTokenAppRequest
from alipay.aop.api.response.AlipayOpenAuthAppApplyResponse import AlipayOpenAuthAppApplyResponse

# app支付
from alipay.aop.api.domain.AlipayFundTransAppPayModel import AlipayFundTransAppPayModel
from alipay.aop.api.request.AlipayFundTransAppPayRequest import AlipayFundTransAppPayRequest
from alipay.aop.api.response.AlipayFundTransAppPayResponse import AlipayFundTransAppPayResponse

# 打款
from alipay.aop.api.domain.AlipayFundTransUniTransferModel import AlipayFundTransUniTransferModel
from alipay.aop.api.request.AlipayFundTransUniTransferRequest import AlipayFundTransUniTransferRequest
from alipay.aop.api.response.AlipayFundTransUniTransferResponse import AlipayFundTransUniTransferResponse
# 红包退款
from alipay.aop.api.domain.AlipayFundTransRefundModel import AlipayFundTransRefundModel
from alipay.aop.api.request.AlipayFundTransRefundRequest import AlipayFundTransRefundRequest
from alipay.aop.api.response.AlipayFundTransRefundResponse import AlipayFundTransRefundResponse
# 红包流水详细

from alipay.aop.api.domain.AlipayFundTransCommonQueryModel import AlipayFundTransCommonQueryModel
from alipay.aop.api.request.AlipayFundTransCommonQueryRequest import AlipayFundTransCommonQueryRequest
from alipay.aop.api.response.AlipayFundTransCommonQueryResponse import AlipayFundTransCommonQueryResponse

# 异步回调验签
from alipay.aop.api.util.WebUtils import *
from alipay.aop.api.util.SignatureUtils import *
from alipay.aop.api.constant.ParamConstants import *

# 支付宝单独的日志

"""
app登录参数
"""


class AlipayAppAuth:
    def __init__(self):
        pass

    def get_params(self):
        params = dict()
        params['apiname'] = "com.alipay.account.auth"
        params['method'] = "alipay.open.auth.sdk.code.get"
        params['app_id'] = pay_config['appId']
        params[P_VERSION] = "1.0"
        params['sign_type'] = "1.0"
        params['app_name'] = "mc"
        params['biz_type'] = "openservice"
        params['pid'] = pay_config['pid']
        params['product_id'] = "APP_FAST_LOGIN"
        params['scope'] = "kuaijie"
        params['target_id'] = str(uuid.uuid1())
        params['auth_type'] = "AUTHACCOUNT"
        return params


class PayAlipay:
    __alipay_client_config = None

    def __init__(self):
        # 支付宝单独的日志
        self._logger = configure_logger("alipay")
        # 构建支付宝基础服务
        self._client = None
        self._sandbox_debug = pay_config['sandbox_debug']
        self._appId = pay_config['appId']
        self._rsaPrivateKey = pay_config['rsaPrivateKey']
        self._rsaPublickKey = pay_config['rsaPublickKey']
        self._alipay_public_key = pay_config['alipayrsaPublicKey']
        self._alipayCertPublicKey_RSA2 = pay_config['alipayCertPublicKey_RSA2']
        self._alipayRootCert = pay_config['alipayRootCert']
        self._appCertPublicKey = pay_config['appCertPublicKey']

        self.build_client()

    def build_client(self):
        """
        设置配置，包括支付宝网关地址、app_id、应用私钥、支付宝公钥等，其他配置值可以查看AlipayClientConfig的定义。
        """
        alipay_client_config = AlipayCertClientConfig(sandbox_debug=False)
        alipay_client_config.app_id = self._appId
        # pkcs1 私钥字符串 startalk.im_ privatekey.txt
        alipay_client_config.app_private_key = self._rsaPrivateKey
        # 支付宝 公钥 alipayrsaPublicKey.txt
        alipay_client_config.alipay_public_key = self._alipay_public_key

        # 设置应用公钥证书路径 appCertPublicKey_2019090266806439.crt
        alipay_client_config.certPath = pay_config['appCertPublicKey']

        # 设置支付宝公钥证书路径 alipayCertPublicKey_RSA2.crt
        alipay_client_config.AlipayPublicCertPath = pay_config['alipayCertPublicKey_RSA2']

        # 设置支付宝根证书路径 alipayRootCert.crt
        alipay_client_config.RootCertPath = pay_config['alipayRootCert']
        self.__alipay_client_config = alipay_client_config
        """
        得到客户端对象。
        注意，一个alipay_client_config对象对应一个DefaultAlipayClient，定义DefaultAlipayClient对象后，alipay_client_config不得修改，如果想使用不同的配置，请定义不同的DefaultAlipayClient。
        logger参数用于打印日志，不传则不打印，建议传递。
        """
        self._client = DefaultAlipayClient(alipay_client_config=self.__alipay_client_config, logger=self._logger)

    """
    注:如果使用 支付宝app登录则不需要此方法
    https://docs.open.alipay.com/218/105326
    
    拼接支付宝第三方应用授权
    https://docs.open.alipay.com/20160728150111277227/intro
    """

    def build_outh_url(self, qt_user_id):
        if pay_config['sandbox_debug']:
            url = 'https://openauth.alipaydev.com/oauth2/appToAppAuth.htm'
        else:
            url = 'https://openauth.alipay.com/oauth2/appToAppAuth.htm'
        redirect_uri = "%s?user_id=%s" % (pay_config['alipay_callback_oauth'], qt_user_id)
        return "%s?app_id=%s&redirect_uri=%s" % (url, pay_config['appId'], redirect_uri)

    """
    第三方授权同步回调
    https://docs.open.alipay.com/20160728150111277227/intro
    """

    def oauth(self, code=None):
        model = AlipayOpenAuthTokenAppModel()
        model.grant_type = "authorization_code"
        model.code = code
        alipay_request = AlipayOpenAuthTokenAppRequest(biz_model=model)
        response_content = None
        result_dict = {'ret': False, 'msg': "", 'code': 0}
        try:
            response_content = self._client.execute(alipay_request)
        except Exception as e:
            self._logger.error(traceback.format_exc())
        if not response_content:
            result_dict['msg'] = "请求支付宝失败,详查支付宝日志"
            result_dict['code'] = -1
        else:
            # 请求成功解析结果

            # response_content = '{"code":"10000","msg":"Success","app_auth_token":"201908BB39dfdf9d285a492c90b63bdb0cd0cX17","app_refresh_token":"201908BBa9e67c586cfe4208b9974b4f4c3acX17","auth_app_id":"2016093000631729","expires_in":31536000,"re_expires_in":32140800,"tokens":[{"app_auth_token":"201908BB39dfdf9d285a492c90b63bdb0cd0cX17","app_refresh_token":"201908BBa9e67c586cfe4208b9974b4f4c3acX17","auth_app_id":"2016093000631729","expires_in":31536000,"re_expires_in":32140800,"user_id":"2088102177956172"}],"user_id":"2088102177956172"}'

            response2 = json.loads(response_content)

            alipay_response = AlipayOpenAuthAppApplyResponse()
            # 解析响应结果
            alipay_response.parse_response_content(response_content)

            result_dict['ret'] = alipay_response.is_success()
            if result_dict['ret']:
                result_dict['user_id'] = response2['user_id']
                result_dict['app_auth_token'] = alipay_response.app_auth_token
                result_dict['app_refresh_token'] = alipay_response.app_refresh_token
                result_dict['msg'] = alipay_response.msg
                result_dict['expires_in'] = response2['expires_in']
                result_dict['re_expires_in'] = response2['re_expires_in']
            else:
                result_dict['sub_code'] = alipay_response.sub_code
                result_dict['sub_msg'] = alipay_response.sub_msg
                result_dict['code'] = -1
                result_dict['msg'] = "请求支付宝失败,详查支付宝日志"

        return result_dict

    """
    验证异步回调签名是否正确
    sign 与sign_type不参与签名
    要请求的所有数据数字 字典格式
    返回 True|False
    """

    def check_sign(self, **params):
        sign = params.pop('sign', None)  # 取出签名
        params.pop('sign_type')  # 取出签名类型
        sign_content = get_sign_content(params).encode(encoding="UTF-8")
        try:
            # 验证签名并获取结果
            status = verify_with_rsa(self._alipay_public_key, sign_content, sign)
            # 返回验证结果
            return status
        except Exception as e:
            # 如果验证失败，返回假值。
            return False

    """
    支付接口 ，用于支付返给app 客户端请求使用
    https://docs.open.alipay.com/20190111144811460526/quickstart/
    https://docs.open.alipay.com/api_28/alipay.fund.trans.app.pay/
    order_no 订单号不能重复
    request_no 订单资金请求流水号不能重复
    amount 订单金额
    title 订单标题 默认 "发送红包"
    timeout 超时时间 默认30分钟
    
    pay_alipay = PayAlipay()
    request_str = pay_alipay.get_app_pay(order_no='282877775259787048', request_no='282877775259787048',
                                             title='发送红包', amount=5.2, timeout='15m')

    """

    def get_app_pay_bak(self, order_no=None, amount=0.00,
                        alipay_uid=None, title="发送红包"):

        # 对照接口文档，构造请求对象
        model = AlipayFundTransAppPayModel()
        model.out_biz_no = order_no
        model.trans_amount = amount
        model.order_title = title

        model.product_code = "STD_RED_PACKET"
        model.biz_scene = "PERSONAL_PAY"

        model.business_params = {'sub_biz_scene': 'REDPACKET', 'payer_binded_alipay_id': alipay_uid}

        alipay_request = AlipayFundTransAppPayRequest(biz_model=model)

        response_content = self._client.sdk_execute(alipay_request)
        return response_content

    def get_app_pay(self, order_no=None, amount=0.00,
                    alipay_uid=None, title="发送红包"):

        # https://docs.open.alipay.com/20190111144811460526/quickstart/
        # biz_content 不要修改。严格按照文档照抄即可
        biz_content = "{" + \
                      "\"out_biz_no\":\"%s\"," % (order_no) + \
                      "\"trans_amount\":%s," % (str(amount)) + \
                      "\"product_code\":\"STD_RED_PACKET\"," + \
                      "\"biz_scene\":\"PERSONAL_PAY\"," + \
                      "\"order_title\":\"%s\"," % (title) + \
                      "\"business_params\":{\"sub_biz_scene\":\"REDPACKET\",\"payer_binded_alipay_uid\":\"%s\"}" % (
                          alipay_uid) + \
                      "}"

        params = self._client.get_common_params(params={
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'method': "alipay.fund.trans.app.pay",
            'version': "1.0"
        })
        params['biz_content'] = biz_content

        sign_content = get_sign_content(params)

        sign = sign_with_rsa2(self.__alipay_client_config.app_private_key, sign_content,
                              self.__alipay_client_config.charset)
        params['sign'] = sign

        return url_encode(params, self.__alipay_client_config.charset)

    def get_app_aa_pay(self, order_no=None, amount=0.00,
                       alipay_uid=None, title="支付aa", payee_info=None):

        # https://docs.open.alipay.com/20190111144811460526/quickstart/
        # biz_content 不要修改。严格按照文档照抄即可
        # biz_scene 改为 DIRECT_TRANSFER 原为PERSONAL_PAY
        biz_content = "{" + \
                      "\"out_biz_no\":\"%s\"," % (order_no) + \
                      "\"trans_amount\":%s," % (str(amount)) + \
                      "\"product_code\":\"TRANS_ACCOUNT_NO_PWD\"," + \
                      "\"biz_scene\":\"PERSONAL_PAY\"," + \
                      "\"order_title\":\"%s\"," % title + \
                      "\"payer_info\":{" + \
                      "\"identity\":\"%s\"," % alipay_uid + \
                      "\"identity_type\":\"ALIPAY_USER_ID\"" + \
                      "}," + \
                      "\"payee_info\":{" + \
                      "\"identity\":\"%s\"," % payee_info + \
                      "\"identity_type\":\"ALIPAY_USER_ID\"" + \
                      "}" + \
                      "}"
        biz_content = "{" + \
                      "\"out_biz_no\":\"%s\"," % (order_no) + \
                      "\"trans_amount\":%s," % (str(amount)) + \
                      "\"product_code\":\"TRANS_ACCOUNT_NO_PWD\"," + \
                      "\"biz_scene\":\"DIRECT_TRANSFER\"," + \
                      "\"order_title\":\"aa支付\"," + \
                      "\"payer_info\":{" + \
                      "\"identity\":\"%s\"," % str(alipay_uid) + \
                      "\"identity_type\":\"ALIPAY_USER_ID\"" + \
                      "}," + \
                      "\"payee_info\":{" + \
                      "\"identity\":\"%s\"," % (str(payee_info)) + \
                      "\"identity_type\":\"ALIPAY_USER_ID\"" + \
                      "}," + \
                      "\"remark\":\"aa支付\"" + \
                      "}"

        params = self._client.get_common_params(params={
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'method': "alipay.fund.trans.uni.transfer",  # alipay.fund.trans.app.pay
            'version': "1.0"
        })
        params.pop('app_cert_sn')
        params.pop('alipay_root_cert_sn')
        params['biz_content'] = biz_content

        sign_content = get_sign_content(params)

        sign = sign_with_rsa2(self.__alipay_client_config.app_private_key, sign_content,
                              self.__alipay_client_config.charset)
        params['sign'] = sign
        print(params)
        return url_encode(params, self.__alipay_client_config.charset)


    """
     app登录
     https://docs.open.alipay.com/218/105327
    """

    def get_app_auth(self):

        params = {
            "apiname": "com.alipay.account.auth",
            'method': "alipay.open.auth.sdk.code.get",
            "app_id": pay_config['appId'],
            'app_name': "mc",
            'biz_type': "openservice",
            'pid': pay_config['pid'],
            'product_id': "APP_FAST_LOGIN",
            'scope': "kuaijie",
            'target_id': hashlib.md5(str(uuid.uuid4()).encode(encoding='UTF-8')).hexdigest(),
            'auth_type': "AUTHACCOUNT",
            'sign_type': self.__alipay_client_config.sign_type,
        }
        sign_content = get_sign_content(params)

        sign = sign_with_rsa2(self.__alipay_client_config.app_private_key, sign_content,
                              self.__alipay_client_config.charset)
        params['sign'] = sign

        return url_encode(params, self.__alipay_client_config.charset)

    """
    红包打款接口,用于抢到红包， 或者 返回AA使用
    
    将某一个红包进行拆解并打款给用户，即用户领取红包
    参考  alipay.fund.trans.uni.transfer
    https://docs.open.alipay.com/20190111144811460526/quickstart/
    https://docs.open.alipay.com/api_28/alipay.fund.trans.uni.transfer/
    抢到红包打款接口
    
    返回ret false 时 有两种情况。 一种是请求接口出现问题， 一种是 接口返回错误
    code = -1 时 请求接口失败
    
    
    order_no 订单号不能重复
    payee_logon_id 拆红包的人支付宝uid
    original_order_id 红包的或AA的支付宝订单号
    amount 订单金额
    title 订单标题 默认 "发送红包"
    
    pay_alipay = PayAlipay()
    api_result = pay_alipay.disburse(order_no='282877775259787048', payee_logon_id='22222222',
                                         original_order_id='282877775259787048', 
                                         title='发送红包', amount=5.2)

    """

    def disburse(self, order_no=None, original_order_id=None, amount=0.00, payee_logon_id=None,
                 title="红包打款"):
        # 对照接口文档，构造请求对象
        model = AlipayFundTransUniTransferModel()

        model.out_biz_no = order_no
        model.trans_amount = amount
        model.product_code = "STD_RED_PACKET"
        #model.biz_scene = "DIRECT_TRANSFER"
        model.biz_scene = "PERSONAL_COLLECTION"
        model.payee_info = {'identity': payee_logon_id, 'identity_type': "ALIPAY_USER_ID"}
        model.original_order_id = original_order_id

        model.order_title = title

        model.business_params = json.dumps({'sub_biz_scene': 'REDPACKET'},
                                           ensure_ascii=False)

        alipay_request = AlipayFundTransUniTransferRequest(biz_model=model)
        response_content = None
        result_dict = {'ret': False, 'msg': "", 'code': 0}

        try:
            response_content = self._client.execute(alipay_request)
        except Exception as e:
            self._logger.error(traceback.format_exc())
        if not response_content:
            result_dict['msg'] = "请求支付宝失败,详查支付宝日志1"
            result_dict['code'] = -1
        else:
            # 请求成功解析结果
            alipay_response = AlipayFundTransUniTransferResponse()
            # 解析响应结果
            alipay_response.parse_response_content(response_content)

            result_dict['ret'] = alipay_response.is_success()
            if result_dict['ret']:
                result_dict['order_id'] = alipay_response.order_id
                result_dict['out_order_no'] = alipay_response.out_biz_no
                result_dict['status'] = alipay_response.status
            else:
                result_dict['sub_code'] = alipay_response.sub_code
                result_dict['sub_msg'] = alipay_response.sub_msg
                result_dict['code'] = -1
                result_dict['msg'] = "请求支付宝失败,详查支付宝日志2"

        return result_dict

    """
    红包退款 资金原路退回，如将红包中未领取的金额退还给红包发送者
    https://docs.open.alipay.com/20190111144811460526/quickstart/
    https://docs.open.alipay.com/api_28/alipay.fund.trans.refund/
     alipay.fund.trans.refund
    request_no 唯一，一笔资金多次请求需要用同一个订单 号
    order_id  支付宝的资金授权订单号，即之前发红包时产生的支付宝订单号
    amount 退款金额
    remark 退款描述 默认“红包退款”
    qtalk 红包默认24领取时间24小时，24小时后退款
    注：支付宝默认48小时+1分钟自动退款
      默认退款会触发通知 
    https://www.merchant.com/receive_notify.htm?notify_type=trade_status_sync&notify_id=91722adff935e8cfa58b3aabf4dead6ibe&notify_time=2017-02-16 21:46:15&sign_type=RSA2&sign=WcO+t3D8Kg71dTlKwN7r9PzUOXeaBJwp8/FOuSxcuSkXsoVYxBpsAidprySCjHCjmaglNcjoKJQLJ28/Asl93joTW39FX6i07lXhnbPknezAlwmvPdnQuI01HZsZF9V1i6ggZjBiAd5lG8bZtTxZOJ87ub2i9GuJ3Nr/NUc9VeY=&auth_no=null&out_order_no=null&operation_id=null&out_request_no=null&operation_type=null&amount=null&status=null&gmt_create=null&gmt_trans=null&payer_logon_id=null&payer_user_id=null

    pay_alipay = PayAlipay()
    api_result = pay_alipay.refund(request_no="282877775259787048", auth_no="282877775259787048",
                                       amount=100.0, remark="红包退款")
     
    测试用
    response_content = '{"code":"10000","msg":"Success","auth_no":"2014070800002001550000014417","out_order_no":"4977164666634053","operation_id":"2014070800032850551","out_request_no":"2014070700166653","amount":0.12,"status":"SUCCESS","gmt_trans":"2014-09-15 11:23:04"}'
    """

    def refund(self, request_no=None, order_id=None, amount=0.00, remark="红包退款"):
        # 对照接口文档，构造请求对象
        model = AlipayFundTransRefundModel()
        model.out_request_no = request_no
        model.order_id = order_id
        model.refund_amount = amount
        model.remark = remark

        alipay_request = AlipayFundTransRefundRequest(biz_model=model)
        response_content = None

        result_dict = {'ret': False, 'msg': "", 'code': 0}
        try:
            response_content = self._client.execute(alipay_request)
        except Exception as e:
            self._logger.error(traceback.format_exc())
        if not response_content:
            result_dict['msg'] = "请求支付宝失败,详查支付宝日志!"
            result_dict['code'] = -1
        else:
            # 请求成功解析结果
            alipay_response = AlipayFundTransRefundResponse()
            # 解析响应结果
            alipay_response.parse_response_content(response_content)

            result_dict['ret'] = alipay_response.is_success()
            if result_dict['ret']:
                result_dict['refund_order_id'] = alipay_response.refund_order_id
                result_dict['order_id'] = alipay_response.order_id
                result_dict['out_request_no'] = alipay_response.out_request_no
                result_dict['refund_amount'] = alipay_response.refund_amount
                result_dict['status'] = alipay_response.status
                result_dict['refund_date'] = alipay_response.refund_date
            else:
                result_dict['sub_code'] = alipay_response.sub_code
                result_dict['sub_msg'] = alipay_response.sub_msg

            result_dict['code'] = alipay_response.code
            result_dict['msg'] = alipay_response.msg

        return result_dict

    """
    查询红包详细，根据支付宝的授权订单号
    https://docs.open.alipay.com/api_28/alipay.fund.trans.common.query/
    https://docs.open.alipay.com/20190111144811460526/quickstart/#%E5%8D%95%E6%8D%AE%E6%9F%A5%E8%AF%A2%E6%8E%A5%E5%8F%A3-alipayfundtranscommonquery
    """

    def operation_query(self, order_id=None):

        model = AlipayFundTransCommonQueryModel()
        model.order_id = order_id
        model.product_code = "STD_RED_PACKET"
        model.biz_scene = "PERSONAL_PAY"
        alipay_request = AlipayFundTransCommonQueryRequest(biz_model=model)
        response_content = None

        result_dict = {'ret': False, 'msg': "", 'code': 0}
        try:
            response_content = self._client.execute(alipay_request)
        except Exception as e:
            self._logger.error(traceback.format_exc())
        if not response_content:
            result_dict['msg'] = "请求支付宝失败,详查支付宝日志"
            result_dict['code'] = -1
        else:
            # 请求成功解析结果
            alipay_response = AlipayFundTransCommonQueryResponse()
            # 解析响应结果
            alipay_response.parse_response_content(response_content)

            result_dict['ret'] = alipay_response.is_success()
            if result_dict['ret']:
                result_dict['order_id'] = alipay_response.order_id
                result_dict['out_order_no'] = alipay_response.out_biz_no
                result_dict['status'] = alipay_response.status
                """
                SUCCESS：转账成功；
                WAIT_PAY：等待支付；
                CLOSED：订单超时关闭 |
                """
            else:
                result_dict['sub_code'] = alipay_response.sub_code
                result_dict['sub_msg'] = alipay_response.sub_msg

            result_dict['code'] = alipay_response.code
            result_dict['msg'] = alipay_response.msg

        return result_dict
