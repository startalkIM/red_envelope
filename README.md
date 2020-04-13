
### **红包使用步骤**:
    1.在支付宝开发平台申请"现金红包"应用
    2.支付宝文件相关参数替换
    3.修改.ini文件配置
    4.启动/停止 程序

####  **在支付宝开发平台申请"现金红包"应用**:
    一.产品介绍:https://docs.open.alipay.com/20190111144811460526/intro
    二.登录支付宝账号(企业账号):https://openhome.alipay.com/platform/home.htm
    三.创建"现金红包"应用:https://openhome.alipay.com/platform/appManage.htm#/apps
        1.选择开发者中心-->网页&移动应用-->支付接入-->应用名称,应用图标,应用类型(选择”移动应用)
        2.功能列表:添加功能-->搜索”现金红包” 并添加
        3.开发设置:
            (1).接口加签方式:
                 * 在https://docs.open.alipay.com/291/106097,下载支付宝开放平台开发助手工具并安装
                 * 打开”支付宝开放平台开发助手”:生成密钥(选择PKCS8,2048,生成密钥)-->应用私钥需要进行格式转换,转PKCS1-->保存startalk.im_privatekey_pkcs1.txt中-->获取CSR文件(选择PKCS1)-->上传公钥
                 * 接口加签方式设置-->公钥-->保存"支付宝公钥"在文档 alipayrsaPublicKey.txt 中-->更换应用公钥-->选择”公钥证书”,上传CSR文件
                 * 上传公钥证书成功之后,下载证书并保存:
                     * 应用公钥证书:appCertPublicKey.crt
                     * 支付宝公钥证书:alipayCertPublicKey_RSA2.crt
                     * 支付宝根证书:alipayRootCert.crt
            (2).应用网关-->设置
            (3).授权回调地址-->设置:HOST+'/red_envelope/oauth'
        4.提交审核
        
#### **支付宝文件相关参数替换**:
    替换支付相关文件内容:/conf/alipaycert
    1.应用私钥:startalk.im_privatekey_pkcs1.txt     
       参数:rsaPrivateKey
    2.支付宝公钥证书:alipayCertPublicKey_RSA2.crt
       参数:alipayCertPublicKey_RSA2
    3.支付宝根证书:alipayRootCert.crt
       参数:alipayRootCert
    4.应用公钥证书:appCertPublicKey.crt
       参数:appCertPublicKey
    5.支付宝公钥:alipayrsaPublicKey.txt
       参数:alipayrsaPublicKey
    
#### **修改.ini文件配置**:
    替换文件参数:/conf/configure.ini  
    1.修改ckey验证接口:
       参数:AUTH_CKEY_URL
    2.qtalk发消息接口:
       参数:SEND_URL
    3.支付相关报警用户:
       参数:ALERT_USER_ID(支付宝开发平台申请账号)
    4.在https://openhome.alipay.com/platform/accountSetting.htm 
      * 账户管理-->合作伙伴管理-->PID:  
        参数:ALIPAY_PID
      * 密钥管理-->开放平台密钥-->APPID:  
        参数: ALIPAY_APPID
    5.申请的域名:
       参数:HOST(如http://im.qunar.com)

          
    
       
#### **启动/停止 程序**:  
    完成上述配置和参数设置
    1.环境python3.7
    2.source /startalk/qtalk_search/venv/bin/activate 进入虚拟环境
    3.pip3 install -r requirement.txt
    4.加入发送红包,拆红包,退红包的定时任务:
       # crontab ./sudo_crontab.txt
       查看定时任务启动:
       # crontab -e
    5.启动:
       # ./red_envelope.sh
    6.停止程序:
       # ./stop.sh
