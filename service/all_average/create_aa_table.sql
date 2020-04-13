-- --用户支付帐户绑定关系表
-- CREATE TABLE public.host_users_pay_account
-- (
--    id bigserial PRIMARY KEY,
--    host_id bigint,
--    user_id varchar(64),
--    alipay_login_account varchar(64),
--    alipay_bind_time timestamptz NOT NULL DEFAULT now(),
--    alipay_update_time timestamptz NOT NULL DEFAULT now()
-- );
--
--
-- COMMENT ON TABLE public.host_users_pay_account IS '用户支付帐户绑定关系,如需要支持其他支持，可扩展字段';
--
-- COMMENT ON COLUMN public.host_users_pay_account.id IS '自增id';
-- COMMENT ON COLUMN public.host_users_pay_account.host_id IS '域id，关联host_info id';
-- COMMENT ON COLUMN public.host_users_pay_account.user_id IS '用户id即qtalk用户名';
-- COMMENT ON COLUMN public.host_users_pay_account.alipay_login_account IS '支付宝的登录帐户';
-- COMMENT ON COLUMN public.host_users_pay_account.alipay_bind_time IS '支付宝帐户绑定时间';
-- COMMENT ON COLUMN public.host_users_pay_account.alipay_update_time IS '支付宝帐户最后更新时间';
--
--
-- CREATE UNIQUE INDEX  ON public.host_users_pay_account (host_id,user_id);

--aa记录表
CREATE TABLE public.all_average
(
  id bigserial PRIMARY KEY,
  host_id bigint,
  organizer varchar(64) NOT NULL,
  payee_account varchar(64),
  members text NOT NULL,
  aa_type varchar(16) NOT NULL DEFAULT 'normal'::varchar,
  credit numeric(7,2) NOT NULL DEFAULT 0.0,
  amount numeric(7,2) NOT NULL DEFAULT 0.0,
  aa_number smallint NOT NULL,
  paid_number smallint NOT NULL DEFAULT 0,
  aa_content varchar(100) NOT NULL DEFAULT ''::varchar,
  expire_time timestamptz NOT NULL,
  group_chat_id varchar(64),
  create_time timestamptz NOT NULL DEFAULT now(),
  update_time timestamptz NOT NULL DEFAULT now(),
  status smallint not null default 0
);


COMMENT ON TABLE public.all_average IS 'aa表';

COMMENT ON COLUMN public.all_average.id IS '自增id';
COMMENT ON COLUMN public.all_average.host_id IS '域id，关联host_info id';
COMMENT ON COLUMN public.all_average.organizer IS '发起者id即qtalk用户名';
COMMENT ON COLUMN public.all_average.members IS '需要支付aa的人';
COMMENT ON COLUMN public.all_average.payee_account IS '收款的帐号';


COMMENT ON COLUMN public.all_average.aa_type IS 'aa类型,normal普通aa，定额,customize定额aa';
COMMENT ON COLUMN public.all_average.credit IS 'aa总金额';
COMMENT ON COLUMN public.all_average.amount IS 'aa已经收到的金额, 包含收款者本身';
COMMENT ON COLUMN public.all_average.aa_number IS 'aa的个数';
COMMENT ON COLUMN public.all_average.paid_number IS '已付款的个数';
COMMENT ON COLUMN public.all_average.aa_content IS 'aa内容';

-- COMMENT ON COLUMN public.all_average.order_id IS 'aa对应的订单id order_list id';
COMMENT ON COLUMN public.all_average.expire_time IS 'aa过期时间，默认24小时过期';


COMMENT ON COLUMN public.all_average.group_chat_id IS 'aa对应的聊天群或用户id，用于签权';
COMMENT ON COLUMN public.all_average.create_time IS '创建时间';
COMMENT ON COLUMN public.all_average.update_time IS '最后更新时间';

COMMENT ON COLUMN public.all_average.status IS 'aa状态， 0为新建， 1为支付中， 2为收款完成， 3为已停止';

CREATE INDEX ON public.all_average (host_id,organizer);


--aa支付记录表


CREATE TABLE public.all_average_draw_record
(
  id bigserial PRIMARY KEY,
  host_id bigint,
  payer varchar(64) ,
  order_id bigint, -- 订单id
  all_average_id bigint NOT NULL,
  credit numeric(7,2) NOT NULL DEFAULT 0.0,
  paid_time timestamptz,
  has_transfer smallint NOT NULL DEFAULT 0,
  transfer_order_line varchar(64),
  transfer_time timestamptz
);

COMMENT ON TABLE public.all_average_draw_record IS 'aa支付记录表';
COMMENT ON COLUMN public.all_average_draw_record.host_id IS '域id，关联host_info id';
COMMENT ON COLUMN public.all_average_draw_record.payer IS '用户id即qtalk用户名';

COMMENT ON COLUMN public.all_average_draw_record.all_average_id IS 'aaid,对应的 all_average id';
COMMENT ON COLUMN public.all_average_draw_record.credit IS '应付金额';
COMMENT ON COLUMN public.all_average_draw_record.paid_time IS '付aa时间';

COMMENT ON COLUMN public.all_average_draw_record.has_transfer IS '是否已转帐 ,0未转,1已转';
COMMENT ON COLUMN public.all_average_draw_record.transfer_order_line IS '转帐对应的order_trace 的order_line';
COMMENT ON COLUMN public.all_average_draw_record.transfer_time IS '转帐时间';

--保证同一用户同一aa只能抢一次
CREATE UNIQUE INDEX ON public.all_average_draw_record (host_id,payer,all_average_id);
CREATE INDEX ON public.all_average_draw_record (has_transfer);
CREATE INDEX ON public.all_average_draw_record (all_average_id);




-- --aa退款记录 -- 如果退款时间超过红过过期时间 + 10m、要手动对帐
-- CREATE TABLE public.all_average_refund_handled_data
-- (
--   id bigserial PRIMARY KEY,
--   order_id bigint NOT NULL, -- 订单id
--   refund_money numeric(7,2) NOT NULL,
--   create_time timestamptz DEFAULT now(),
--   state varchar(255) NOT NULL
-- );
--
--
-- COMMENT ON TABLE public.all_average_refund_handled_data IS 'aa退款记录';
-- COMMENT ON COLUMN public.all_average_refund_handled_data.id IS '自增id';
-- COMMENT ON COLUMN public.all_average_refund_handled_data.order_id IS 'aa对应的订单id order_list id';
-- COMMENT ON COLUMN public.all_average_refund_handled_data.refund_money IS '退款金额';
-- COMMENT ON COLUMN public.all_average_refund_handled_data.create_time IS '创建时间';
-- COMMENT ON COLUMN public.all_average_refund_handled_data.state IS '处理状态 new|done';
--
--
-- CREATE INDEX ON public.all_average_refund_handled_data (order_id, state);



-- --订单表
-- CREATE TABLE public.order_list
-- (
--   id bigserial PRIMARY KEY,
--
--   order_type varchar(16) NOT NULL,
--   pay_channel varchar(64),
--   pay_account varchar(64),
--
--   credit numeric(7,2) NOT NULL DEFAULT 0.00, -- 订单金额
--   remain_credit numeric(7,2) NOT NULL DEFAULT 0.00, -- 剩余金额
--   refund_credit numeric(7,2) NOT NULL DEFAULT 0.00, -- 退款金额
--
--   order_no varchar(64),--订单号
--   order_line varchar(64), -- 交易流水号
--   refund_order_line varchar(64), -- 退款交易流水号
--
--   pay_order_no varchar(128), -- 支付渠道授权订单号 auth_no
--   pay_order_line varchar(128), -- 支付渠道授权资金操作流水号 operation_id
--
--
--   state varchar(16) NOT NULL, -- 订单状态 unpay|pay|refund|partial_refund|re_balance_ing|re_balance_ok
--   order_comments jsonb, -- 订单备注
--
--   create_time timestamptz NOT NULL DEFAULT now(), -- 订单创建时间
--   pay_time timestamptz, -- 订单支付时间
--   cancel_time timestamptz, -- 订单取消时间
--   refund_time timestamptz -- 订单退款时间
-- );
--
-- COMMENT ON COLUMN public.order_list.id IS '订单id';
-- COMMENT ON COLUMN public.order_list.order_type IS '订单类型:all_average=发aa,return_balance=退款,aa=AA';
--
-- COMMENT ON COLUMN public.order_list.pay_channel IS '支付渠道 alipay|wechat';
-- COMMENT ON COLUMN public.order_list.pay_account IS '支付的帐号';
--
-- COMMENT ON COLUMN public.order_list.pay_order_no IS '支付渠道授权订单号 auth_no';
-- COMMENT ON COLUMN public.order_list.pay_order_line IS '支付渠道授权资金操作流水号 operation_id';
--
--
-- COMMENT ON COLUMN public.order_list.credit IS '订单金额';
-- COMMENT ON COLUMN public.order_list.remain_credit IS '剩余金额';
-- COMMENT ON COLUMN public.order_list.refund_credit IS '退款金额';
-- COMMENT ON COLUMN public.order_list.order_no IS '订单号';
-- COMMENT ON COLUMN public.order_list.order_line IS '交易流水号';
-- COMMENT ON COLUMN public.order_list.refund_order_line IS '退款交易流水号';
--
-- COMMENT ON COLUMN public.order_list.state IS '订单状态 unpay|pay|refund|partial_refund|re_balance_ing|re_balance_ok';
-- COMMENT ON COLUMN public.order_list.order_comments IS '订单备注相关，例如退款对应的订单id, aa退订';
--
-- COMMENT ON COLUMN public.order_list.create_time IS '订单创建时间';
-- COMMENT ON COLUMN public.order_list.pay_time IS '订单支付时间';
-- COMMENT ON COLUMN public.order_list.cancel_time IS '订单取消时间';
-- COMMENT ON COLUMN public.order_list.refund_time IS '订单退款时间';
--
--
-- CREATE INDEX ON public.order_list (order_no);
-- CREATE INDEX ON public.order_list (state);
-- CREATE INDEX ON public.order_list (pay_channel,pay_account);
-- CREATE INDEX ON public.order_list (pay_order_no);



-- 可以存到这里面 共用同一张表
-- --订单流水表
-- CREATE TABLE public.order_trace
-- (
--   id bigserial PRIMARY KEY,
--   order_id bigint NOT NULL, -- 订单id order_list id
--   order_line varchar(64) NOT NULL, -- 交易流水号
--   pay_channel varchar(64), -- 支付渠道 alipay|wechat
--   pay_account varchar(64), -- 支付的帐号
--
--   pay_status varchar(20), -- 支付状态
--   pay_order_no varchar(128), -- 支付渠道授权订单号
--   pay_order_line varchar(128), -- 支付渠道授权资金操作流水号
--
--   credit numeric(7,2)  NOT NULL DEFAULT 0.00, -- 金额
--   op varchar(16) NOT NULL,
--   op_time timestamptz NOT NULL DEFAULT now(), -- 操作时间
--   trace_comments jsonb -- 用于存储请求返回来的信息
-- );
--
-- COMMENT ON COLUMN public.order_trace.id IS '自增id';
-- COMMENT ON COLUMN public.order_trace.order_id IS '订单id';
-- COMMENT ON COLUMN public.order_trace.order_line IS '交易流水号';
--
-- COMMENT ON COLUMN public.order_trace.pay_channel IS '支付渠道 alipay|wechat';
-- COMMENT ON COLUMN public.order_trace.pay_account IS '支付的帐号';
--
-- COMMENT ON COLUMN public.order_trace.pay_status IS '支付状态';
-- COMMENT ON COLUMN public.order_trace.pay_order_no IS '支付渠道授权订单号';
-- COMMENT ON COLUMN public.order_trace.pay_order_line IS '支付渠道授权资金操作流水号';
--
-- COMMENT ON COLUMN public.order_trace.credit IS '支付金额';
-- COMMENT ON COLUMN public.order_trace.op IS '操作 pay|refund|return_balance|';
--
-- COMMENT ON COLUMN public.order_trace.op_time IS '操作时间';
-- COMMENT ON COLUMN public.order_trace.trace_comments IS '用于存储请求返回来的信息';
--
--
-- CREATE INDEX ON public.order_trace (order_id);
-- CREATE INDEX ON public.order_trace (order_line);
-- CREATE INDEX ON public.order_trace (pay_channel);
-- CREATE INDEX ON public.order_trace (pay_account);
-- CREATE INDEX ON public.order_trace (pay_status);
-- CREATE INDEX ON public.order_trace (pay_order_no);