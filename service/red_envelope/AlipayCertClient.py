#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on 2017-12-20

@author: liuqun
"""
import datetime
import uuid
from OpenSSL import crypto
import hashlib
from alipay.aop.api.constant.ParamConstants import *
from alipay.aop.api.util.WebUtils import *
from alipay.aop.api.util.SignatureUtils import *
from alipay.aop.api.util.CommonUtils import *
from alipay.aop.api.util.EncryptUtils import *

P_ALIPAY_ROOT_CERT_SN = "alipay_root_cert_sn"
COMMON_PARAM_KEYS.add(P_ALIPAY_ROOT_CERT_SN)

P_APP_CERT_SN = "app_cert_sn"
COMMON_PARAM_KEYS.add(P_APP_CERT_SN)
P_ALIPAY_SDK = 'alipay_sdk'
COMMON_PARAM_KEYS.add(P_ALIPAY_SDK)

"""
蚂蚁金服开放平台接入客户端

alipay_client_config = AlipayCertClientConfig(sandbox_debug=False)
alipay_client_config.app_id = pay_config['appId']
# pkcs1 私钥字符串 startalk.im_ privatekey.txt
alipay_client_config.app_private_key = pay_config['rsaPrivateKey']
# 支付宝 公钥 alipayrsaPublicKey.txt
alipay_client_config.alipay_public_key = pay_config['alipayrsaPublicKey']

# 设置应用公钥证书路径 appCertPublicKey_2019090266806439.crt
alipay_client_config.certPath = pay_config['appCertPublicKey']

# 设置支付宝公钥证书路径 alipayCertPublicKey_RSA2.crt
alipay_client_config.AlipayPublicCertPath = pay_config['alipayCertPublicKey_RSA2']

# 设置支付宝根证书路径 alipayRootCert.crt
alipay_client_config.RootCertPath = pay_config['alipayRootCert']

accc = AlipayCertClient(alipay_client_config=alipay_client_config)
a = accc.getRootCertSN()
print(a)
a = accc.getCertSN()
print(a)

"""


class AlipayCertClient(object):
    """
    alipay_client_config：客户端配置，包含app_id、应用私钥、支付宝公钥等
    logger：日志对象，客户端执行信息会通过此日志对象输出
    alipay_client_config 需要使用自定义的AlipayCertClientConfig
    """

    def __init__(self, alipay_client_config, logger=None):
        self.__config = alipay_client_config
        self.__logger = logger

    def get_common_params(self, params):
        return self.__get_common_params(params)

    """
    内部方法，从params中抽取公共参数
    """

    def __get_common_params(self, params):
        common_params = dict()
        common_params[P_TIMESTAMP] = params[P_TIMESTAMP]
        common_params[P_APP_ID] = self.__config.app_id
        common_params[P_METHOD] = params[P_METHOD]
        common_params[P_CHARSET] = self.__config.charset
        common_params[P_FORMAT] = self.__config.format
        common_params[P_VERSION] = params[P_VERSION]
        common_params[P_SIGN_TYPE] = self.__config.sign_type
        common_params[P_ALIPAY_ROOT_CERT_SN] = self.getRootCertSN()
        common_params[P_APP_CERT_SN] = self.getCertSN()
        common_params[P_ALIPAY_SDK] = "alipay-sdk-java-4.5.0.ALL"

        if self.__config.encrypt_type:
            common_params[P_ENCRYPT_TYPE] = self.__config.encrypt_type
        if has_value(params, P_APP_AUTH_TOKEN):
            common_params[P_APP_AUTH_TOKEN] = params[P_APP_AUTH_TOKEN]
        if has_value(params, P_AUTH_TOKEN):
            common_params[P_AUTH_TOKEN] = params[P_AUTH_TOKEN]
        if has_value(params, P_NOTIFY_URL):
            common_params[P_NOTIFY_URL] = params[P_NOTIFY_URL]
        if has_value(params, P_RETURN_URL):
            common_params[P_RETURN_URL] = params[P_RETURN_URL]
        return common_params

    """
    内部方法，从params中移除公共参数
    """

    def __remove_common_params(self, params):
        if not params:
            return
        for k in COMMON_PARAM_KEYS:
            if k in params:
                params.pop(k)

    """
    内部方法，构造form表单输出结果
    """

    def __build_form(self, url, params):
        form = "<form name=\"punchout_form\" method=\"post\" action=\""
        form += url
        form += "\">\n"
        if params:
            for k, v in params.items():
                if not v:
                    continue
                form += "<input type=\"hidden\" name=\""
                form += k
                form += "\" value=\""
                form += v.replace("\"", "&quot;")
                form += "\">\n"
        form += "<input type=\"submit\" value=\"立即支付\" style=\"display:none\" >\n"
        form += "</form>\n"
        form += "<script>document.forms[0].submit();</script>"
        return form

    """
    内部方法，通过请求request对象构造请求查询字符串和业务参数
    """

    def __prepare_request(self, request):
        common_params, params = self.__prepare_request_params(request)
        query_string = url_encode(common_params, self.__config.charset)
        return query_string, params

    """
    内部方法，通过请求request对象构造SDK请求查询字符串
    """

    def __prepare_sdk_request(self, request):
        common_params, params = self.__prepare_request_params(request)
        allParams = dict()
        allParams.update(common_params)
        allParams.update(params)
        query_string = url_encode(allParams, self.__config.charset)
        return query_string

    """
    内部方法，通过请求request对象构造请求参数
    """

    def __prepare_request_params(self, request):
        THREAD_LOCAL.logger = self.__logger
        params = request.get_params()
        if P_BIZ_CONTENT in params:
            if self.__config.encrypt_type and self.__config.encrypt_key:
                params[P_BIZ_CONTENT] = encrypt_content(params[P_BIZ_CONTENT], self.__config.encrypt_type,
                                                        self.__config.encrypt_key, self.__config.charset)
            else:
                if request.need_encrypt:
                    raise RequestException("接口" + params[P_METHOD] + "必须使用encrypt_type、encrypt_key加密")
        params[P_TIMESTAMP] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        common_params = self.__get_common_params(params)
        all_params = dict()
        all_params.update(params)
        all_params.update(common_params)
        sign_content = get_sign_content(all_params)
        try:
            if self.__config.sign_type and self.__config.sign_type == 'RSA2':
                sign = sign_with_rsa2(self.__config.app_private_key, sign_content, self.__config.charset)
            else:
                sign = sign_with_rsa(self.__config.app_private_key, sign_content, self.__config.charset)
        except Exception as e:
            raise RequestException('[' + THREAD_LOCAL.uuid + ']request sign failed. ' + str(e))
        common_params[P_SIGN] = sign
        self.__remove_common_params(params)

        log_url = self.__config.server_url + '?' + sign_content + "&sign=" + sign
        if THREAD_LOCAL.logger:
            THREAD_LOCAL.logger.info('[' + THREAD_LOCAL.uuid + ']request:' + log_url)

        return common_params, params

    """
    内部方法，解析请求返回结果并做验签
    """

    def __parse_response(self, response_str):
        if PYTHON_VERSION_3:
            response_str = response_str.decode(self.__config.charset)
        if THREAD_LOCAL.logger:
            THREAD_LOCAL.logger.info('[' + THREAD_LOCAL.uuid + ']response:' + response_str)

        response_content = None
        sign = None
        em1 = None
        em2 = None
        has_encrypted = False
        if self.__config.encrypt_type and self.__config.encrypt_key:
            em1 = PATTERN_RESPONSE_ENCRYPT_BEGIN.search(response_str)
            em2 = PATTERN_RESPONSE_SIGN_ENCRYPT_BEGIN.search(response_str)
            if em1 and em2:
                has_encrypted = True
                sign_start_index = em2.start()
                sign_end_index = em2.end()
                while em2:
                    em2 = PATTERN_RESPONSE_SIGN_BEGIN.search(response_str, pos=em2.end())
                    if em2:
                        sign_start_index = em2.start()
                        sign_end_index = em2.end()
                response_content = response_str[em1.end() - 1:sign_start_index + 1]
                if PYTHON_VERSION_3:
                    response_content = response_content.encode(self.__config.charset)
                sign = response_str[sign_end_index:response_str.find("\"", sign_end_index)]
        if not response_content:

            PATTERN_RESPONSE_BEGIN = re.compile(r'(\"[a-zA-z_]+_response\"[ \t\n]*:[ \t\n]*\{)')
            PATTERN_RESPONSE_CERT_SN_BEGIN = re.compile(r'(\}[ \t\n]*,[ \t\n]*\"alipay_cert_sn\"[ \t\n]*:[ \t\n]*\")')
            PATTERN_RESPONSE_SIGN_BEGIN = re.compile(r'(\"[ \t\n]*,[ \t\n]*\"sign\"[ \t\n]*:[ \t\n]*\")')
            m1 = PATTERN_RESPONSE_BEGIN.search(response_str)
            m2 = PATTERN_RESPONSE_CERT_SN_BEGIN.search(response_str)
            m3 = PATTERN_RESPONSE_SIGN_BEGIN.search(response_str)

            sign_start_index = m3.start()
            sign_end_index = m3.end()
            while m3:
                m3 = PATTERN_RESPONSE_SIGN_BEGIN.search(response_str, pos=m3.end())
                if m3:
                    sign_start_index = m3.start()
                    sign_end_index = m3.end()

            sn_start_index = m2.start()
            sn_end_index = m2.end()
            while m2:
                m2 = PATTERN_RESPONSE_CERT_SN_BEGIN.search(response_str, pos=m2.end())
                if m2:
                    sn_start_index = m2.start()
                    sn_end_index = m2.end()

            response_content = response_str[m1.end() - 1:sn_start_index + 1]

            alipay_cert_sn = response_str[sn_end_index:response_str.find("\"", sn_end_index)]

            my_alipay_cert_sn = self.getAlipayPublicCertSN()
            # 校验返回来的证书与本地证书签名是否一致，不一致则抛异常
            if my_alipay_cert_sn != alipay_cert_sn:
                raise ResponseException(
                    '[' + THREAD_LOCAL.uuid + ']check alipay_public cent sn faild ' + self.__config.AlipayPublicCertPath)

            if PYTHON_VERSION_3:
                response_content = response_content.encode(self.__config.charset)
            sign = response_str[sign_end_index:response_str.find("\"", sign_end_index)]
        try:
            verify_res = verify_with_rsa(self.__config.alipay_public_key, response_content, sign)
        except Exception as e:
            raise ResponseException('[' + THREAD_LOCAL.uuid + ']response sign verify failed. ' + str(e) + \
                                    ' ' + response_str)
        if not verify_res:
            raise ResponseException('[' + THREAD_LOCAL.uuid + ']response sign verify failed. ' + response_str)
        response_content = response_content.decode(self.__config.charset)
        if has_encrypted:
            response_content = decrypt_content(response_content[1:-1], self.__config.encrypt_type,
                                               self.__config.encrypt_key, self.__config.charset)
        return response_content

    """
    执行接口请求
    """

    def execute(self, request):
        THREAD_LOCAL.uuid = str(uuid.uuid1())
        headers = {
            'Content-type': 'application/x-www-form-urlencoded;charset=' + self.__config.charset,
            "Cache-Control": "no-cache",
            "Connection": "Keep-Alive",
            "User-Agent": ALIPAY_SDK_PYTHON_VERSION,
            "log-uuid": THREAD_LOCAL.uuid,
        }

        query_string, params = self.__prepare_request(request)
        multipart_params = request.get_multipart_params()

        if multipart_params and len(multipart_params) > 0:
            response = do_multipart_post(self.__config.server_url, query_string, headers, params, multipart_params,
                                         self.__config.charset, self.__config.timeout)
        else:
            response = do_post(self.__config.server_url, query_string, headers, params, self.__config.charset,
                               self.__config.timeout)

        return self.__parse_response(response)

    '''
    得到页面跳转接口的url或表单html
    '''

    def page_execute(self, request, http_method="POST"):
        THREAD_LOCAL.uuid = str(uuid.uuid1())
        url = self.__config.server_url
        pos = url.find("?")
        if pos >= 0:
            url = url[0:pos]

        query_string, params = self.__prepare_request(request)

        if http_method == "GET":
            return url + "?" + query_string + "&" + url_encode(params, self.__config.charset)
        else:
            return self.__build_form(url + "?" + query_string, params)

    '''
    得到sdk调用的参数
    '''

    def sdk_execute(self, request):
        THREAD_LOCAL.uuid = str(uuid.uuid1())
        return self.__prepare_sdk_request(request)

    '''
    获取root 根证书
    获取支付宝签名cn 
    # 必须是pkcs1的证书
    # java 判断 if(c.getSigAlgOID().startsWith("1.2.840.113549.1.1")){
    # https://www.alvestrand.no/objectid/1.2.840.113549.1.1.html
    # oid info
    # http://oid-info.com/get/1.2.840.113549.1.1.1
    '''

    def getRootCertSN(self):
        sign_algorithm_map = {
            "rsaEncryption": "1.2.840.113549.1.1.1",
            "md2WithRSAEncryption": "1.2.840.113549.1.1.2",
            "md4withRSAEncryption": "1.2.840.113549.1.1.3",
            "md5WithRSAEncryption": "1.2.840.113549.1.1.4",
            "sha1-with-rsa-signature": "1.2.840.113549.1.1.5",
            "sha1WithRSAEncryption": "1.2.840.113549.1.1.5",
            "sha-1WithRSAEncryption": "1.2.840.113549.1.1.5",
            "rsaOAEPEncryptionSET": "1.2.840.113549.1.1.6",
            "ripemd160WithRSAEncryption": "1.2.840.113549.1.1.6",
            "id-RSAES-OAEP": "1.2.840.113549.1.1.7",
            "id-mgf1": "1.2.840.113549.1.1.8",
            "id-pSpecified": "1.2.840.113549.1.1.9",
            "rsassa-pss": "1.2.840.113549.1.1.10",
            "sha256WithRSAEncryption": "1.2.840.113549.1.1.11",
        }

        pem = open(self.__config.RootCertPath).read()

        c = pem.split("-----END CERTIFICATE-----")

        all_cert_md5 = []
        for i in c:
            pem_i = i + "-----END CERTIFICATE-----\n"
            try:
                cert = crypto.load_certificate(crypto.FILETYPE_PEM, pem_i)
                is_suuer = cert.get_issuer()
                algorithm = cert.get_signature_algorithm().decode(encoding="utf-8")

                if algorithm in sign_algorithm_map.keys():
                    sn = cert.get_serial_number()
                    name = "CN=%s,OU=%s,O=%s,C=%s" % (is_suuer.CN, is_suuer.OU, is_suuer.O, is_suuer.C)

                    md5 = hashlib.md5(str(name).encode(encoding='UTF-8') + str(sn).encode(encoding='UTF-8')).hexdigest()
                    all_cert_md5.append(md5)
            except Exception as e:
                pass
            else:
                pass
        return "_".join(all_cert_md5)

    '''
    应用公钥sn
    '''

    def getCertSN(self):

        pem = open(self.__config.certPath).read()
        try:
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, pem)
            is_suuer = cert.get_issuer()
            algorithm = cert.get_signature_algorithm().decode(encoding="utf-8")
            sn = cert.get_serial_number()
            name = "CN=%s,OU=%s,O=%s,C=%s" % (is_suuer.CN, is_suuer.OU, is_suuer.O, is_suuer.C)

            return hashlib.md5(str(name).encode(encoding='UTF-8') + str(sn).encode(encoding='UTF-8')).hexdigest()
        except Exception as e:
            pass
        else:
            pass
        return None

    '''
    获取alipay 公钥证书 sn
    '''

    def getAlipayPublicCertSN(self):

        pem = open(self.__config.AlipayPublicCertPath).read()
        try:
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, pem)
            is_suuer = cert.get_issuer()
            algorithm = cert.get_signature_algorithm().decode(encoding="utf-8")
            sn = cert.get_serial_number()
            name = "CN=%s,OU=%s,O=%s,C=%s" % (is_suuer.CN, is_suuer.OU, is_suuer.O, is_suuer.C)

            return hashlib.md5(str(name).encode(encoding='UTF-8') + str(sn).encode(encoding='UTF-8')).hexdigest()
        except Exception as e:
            pass
        else:
            pass
        return None
