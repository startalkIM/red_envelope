--用户支付帐户绑定关系表
CREATE TABLE public.host_users_pay_account
(
   id bigserial PRIMARY KEY,
   host_id bigint,
   user_id varchar(64),
   alipay_login_account varchar(64),
   alipay_bind_time timestamptz NOT NULL DEFAULT now(),
   alipay_update_time timestamptz NOT NULL DEFAULT now()
);


COMMENT ON TABLE public.host_users_pay_account IS '用户支付帐户绑定关系,如需要支持其他支持，可扩展字段';

COMMENT ON COLUMN public.host_users_pay_account.id IS '自增id';
COMMENT ON COLUMN public.host_users_pay_account.host_id IS '域id，关联host_info id';
COMMENT ON COLUMN public.host_users_pay_account.user_id IS '用户id即qtalk用户名';
COMMENT ON COLUMN public.host_users_pay_account.alipay_login_account IS '支付宝的登录帐户';
COMMENT ON COLUMN public.host_users_pay_account.alipay_bind_time IS '支付宝帐户绑定时间';
COMMENT ON COLUMN public.host_users_pay_account.alipay_update_time IS '支付宝帐户最后更新时间';


CREATE UNIQUE INDEX  ON public.host_users_pay_account (host_id,user_id);

--红包记录表
CREATE TABLE public.red_envelope
(
  id bigserial PRIMARY KEY,
  host_id bigint,
  user_id varchar(64),
  red_type varchar(16) NOT NULL DEFAULT 'normal'::varchar,
  credit numeric(7,2) NOT NULL DEFAULT 0.0,
  balance numeric(7,2) NOT NULL DEFAULT 0.0,
  red_number smallint NOT NULL,
  draw_number smallint NOT NULL DEFAULT 0,
  red_content varchar(100) NOT NULL DEFAULT ''::varchar,
  order_id bigint NOT NULL DEFAULT 0,
  expire_time timestamptz NOT NULL,
  group_chat_id varchar[],
  create_time timestamptz NOT NULL DEFAULT now(),
  update_time timestamptz NOT NULL DEFAULT now()
);


COMMENT ON TABLE public.red_envelope IS '红包表';

COMMENT ON COLUMN public.red_envelope.id IS '自增id';
COMMENT ON COLUMN public.red_envelope.host_id IS '域id，关联host_info id';
COMMENT ON COLUMN public.red_envelope.user_id IS '用户id即qtalk用户名';

COMMENT ON COLUMN public.red_envelope.red_type IS '红包类型,normal普通红包，定额,luckly拼手气红包';
COMMENT ON COLUMN public.red_envelope.credit IS '红包金额';
COMMENT ON COLUMN public.red_envelope.balance IS '红包剩余金额';
COMMENT ON COLUMN public.red_envelope.red_number IS '红包的个数';
COMMENT ON COLUMN public.red_envelope.draw_number IS '红包的领取个数';
COMMENT ON COLUMN public.red_envelope.red_content IS '红包内容';

COMMENT ON COLUMN public.red_envelope.order_id IS '红包对应的订单id order_list id';
COMMENT ON COLUMN public.red_envelope.expire_time IS '红包过期时间，默认24小时过期';


COMMENT ON COLUMN public.red_envelope.group_chat_id IS '红包对应的聊天群或用户id，用于签权用户是否能领取';
COMMENT ON COLUMN public.red_envelope.create_time IS '创建时间';
COMMENT ON COLUMN public.red_envelope.update_time IS '最后更新时间';


CREATE INDEX ON public.red_envelope (host_id,user_id);
CREATE INDEX ON public.red_envelope (order_id);


--红包拆成功记录表


CREATE TABLE public.red_envelope_draw_record
(
  id bigserial PRIMARY KEY,
  host_id bigint,
  user_id varchar(64) ,
  red_envelope_id bigint NOT NULL,
  credit numeric(7,2) NOT NULL DEFAULT 0.0,
  draw_time timestamptz NOT NULL DEFAULT now(),
  has_transfer smallint NOT NULL DEFAULT 0,
  transfer_order_line varchar(64),
  transfer_time timestamptz
);

COMMENT ON TABLE public.red_envelope_draw_record IS '拆红包记录表';
COMMENT ON COLUMN public.red_envelope_draw_record.host_id IS '域id，关联host_info id';
COMMENT ON COLUMN public.red_envelope_draw_record.user_id IS '用户id即qtalk用户名';

COMMENT ON COLUMN public.red_envelope_draw_record.red_envelope_id IS '红包id,对应的 red_envelope id';
COMMENT ON COLUMN public.red_envelope_draw_record.credit IS '拆红包的金额';
COMMENT ON COLUMN public.red_envelope_draw_record.draw_time IS '抢红包时间';

COMMENT ON COLUMN public.red_envelope_draw_record.has_transfer IS '是否已转帐 ,0未转,1已转';
COMMENT ON COLUMN public.red_envelope_draw_record.transfer_order_line IS '转帐对应的order_trace 的order_line';
COMMENT ON COLUMN public.red_envelope_draw_record.transfer_time IS '转帐时间';

--保证同一用户同一红包只能抢一次
CREATE UNIQUE INDEX ON public.red_envelope_draw_record (host_id,user_id,red_envelope_id);
CREATE INDEX ON public.red_envelope_draw_record (has_transfer);
CREATE INDEX ON public.red_envelope_draw_record (red_envelope_id);




--红包退款记录 -- 如果退款时间超过红过过期时间 + 10m、要手动对帐
CREATE TABLE public.red_envelope_refund_handled_data
(
  id bigserial PRIMARY KEY,
  order_id bigint NOT NULL, -- 订单id
  refund_money numeric(7,2) NOT NULL,
  create_time timestamptz DEFAULT now(),
  state varchar(255) NOT NULL
);


COMMENT ON TABLE public.red_envelope_refund_handled_data IS '红包退款记录';
COMMENT ON COLUMN public.red_envelope_refund_handled_data.id IS '自增id';
COMMENT ON COLUMN public.red_envelope_refund_handled_data.order_id IS '红包对应的订单id order_list id';
COMMENT ON COLUMN public.red_envelope_refund_handled_data.refund_money IS '退款金额';
COMMENT ON COLUMN public.red_envelope_refund_handled_data.create_time IS '创建时间';
COMMENT ON COLUMN public.red_envelope_refund_handled_data.state IS '处理状态 new|done';


CREATE INDEX ON public.red_envelope_refund_handled_data (order_id, state);



--订单表
CREATE TABLE public.order_list
(
  id bigserial PRIMARY KEY,
  aid bigint,
  order_type varchar(16) NOT NULL,
  pay_channel varchar(64),
  pay_account varchar(64),

  credit numeric(7,2) NOT NULL DEFAULT 0.00, -- 订单金额
  remain_credit numeric(7,2) NOT NULL DEFAULT 0.00, -- 剩余金额
  refund_credit numeric(7,2) NOT NULL DEFAULT 0.00, -- 退款金额

  order_no varchar(64),--订单号
  order_line varchar(64), -- 交易流水号
  refund_order_line varchar(64), -- 退款交易流水号

  pay_order_no varchar(128), -- 支付渠道授权订单号 auth_no
  pay_order_line varchar(128), -- 支付渠道授权资金操作流水号 operation_id


  state varchar(16) NOT NULL, -- 订单状态 unpay|pay|refund|partial_refund|re_balance_ing|re_balance_ok
  order_comments jsonb, -- 订单备注

  create_time timestamptz NOT NULL DEFAULT now(), -- 订单创建时间
  pay_time timestamptz, -- 订单支付时间
  cancel_time timestamptz, -- 订单取消时间
  refund_time timestamptz -- 订单退款时间
);

COMMENT ON COLUMN public.order_list.id IS '订单id';
comment on column public.order_list.aid IS 'aaID，如果是红包则忽略';
COMMENT ON COLUMN public.order_list.order_type IS '订单类型:red_envelope=发红包,return_balance=退款,aa=AA';

COMMENT ON COLUMN public.order_list.pay_channel IS '支付渠道 alipay|wechat';
COMMENT ON COLUMN public.order_list.pay_account IS '支付的帐号';

COMMENT ON COLUMN public.order_list.pay_order_no IS '支付渠道授权订单号 auth_no';
COMMENT ON COLUMN public.order_list.pay_order_line IS '支付渠道授权资金操作流水号 operation_id';


COMMENT ON COLUMN public.order_list.credit IS '订单金额';
COMMENT ON COLUMN public.order_list.remain_credit IS '剩余金额';
COMMENT ON COLUMN public.order_list.refund_credit IS '退款金额';
COMMENT ON COLUMN public.order_list.order_no IS '订单号';
COMMENT ON COLUMN public.order_list.order_line IS '交易流水号';
COMMENT ON COLUMN public.order_list.refund_order_line IS '退款交易流水号';

COMMENT ON COLUMN public.order_list.state IS '订单状态 unpay|pay|refund|partial_refund|re_balance_ing|re_balance_ok';
COMMENT ON COLUMN public.order_list.order_comments IS '订单备注相关，例如退款对应的订单id, aa退订';

COMMENT ON COLUMN public.order_list.create_time IS '订单创建时间';
COMMENT ON COLUMN public.order_list.pay_time IS '订单支付时间';
COMMENT ON COLUMN public.order_list.cancel_time IS '订单取消时间';
COMMENT ON COLUMN public.order_list.refund_time IS '订单退款时间';


CREATE INDEX ON public.order_list (order_no);
CREATE INDEX ON public.order_list (state);
CREATE INDEX ON public.order_list (pay_channel,pay_account);
CREATE INDEX ON public.order_list (pay_order_no);




--订单流水表
CREATE TABLE public.order_trace
(
  id bigserial PRIMARY KEY,
  order_id bigint NOT NULL, -- 订单id order_list id
  order_line varchar(64) NOT NULL, -- 交易流水号
  pay_channel varchar(64), -- 支付渠道 alipay|wechat
  pay_account varchar(64), -- 支付的帐号

  pay_status varchar(20), -- 支付状态
  pay_order_no varchar(128), -- 支付渠道授权订单号
  pay_order_line varchar(128), -- 支付渠道授权资金操作流水号

  credit numeric(7,2)  NOT NULL DEFAULT 0.00, -- 金额
  op varchar(16) NOT NULL,
  op_time timestamptz NOT NULL DEFAULT now(), -- 操作时间
  trace_comments jsonb -- 用于存储请求返回来的信息
);

COMMENT ON COLUMN public.order_trace.id IS '自增id';
COMMENT ON COLUMN public.order_trace.order_id IS '订单id';
COMMENT ON COLUMN public.order_trace.order_line IS '交易流水号';

COMMENT ON COLUMN public.order_trace.pay_channel IS '支付渠道 alipay|wechat';
COMMENT ON COLUMN public.order_trace.pay_account IS '支付的帐号';

COMMENT ON COLUMN public.order_trace.pay_status IS '支付状态';
COMMENT ON COLUMN public.order_trace.pay_order_no IS '支付渠道授权订单号';
COMMENT ON COLUMN public.order_trace.pay_order_line IS '支付渠道授权资金操作流水号';

COMMENT ON COLUMN public.order_trace.credit IS '支付金额';
COMMENT ON COLUMN public.order_trace.op IS '操作 pay|refund|return_balance|';

COMMENT ON COLUMN public.order_trace.op_time IS '操作时间';
COMMENT ON COLUMN public.order_trace.trace_comments IS '用于存储请求返回来的信息';


CREATE INDEX ON public.order_trace (order_id);
CREATE INDEX ON public.order_trace (order_line);
CREATE INDEX ON public.order_trace (pay_channel);
CREATE INDEX ON public.order_trace (pay_account);
CREATE INDEX ON public.order_trace (pay_status);
CREATE INDEX ON public.order_trace (pay_order_no);