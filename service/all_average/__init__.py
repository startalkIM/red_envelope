#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
表结构
————————— all average —————————
    Column     |           Type           | Collation | Nullable |                 Default                 | Storage  | Stats target | Description
---------------+--------------------------+-----------+----------+-----------------------------------------+----------+--------------+-------------
 id            | bigint                   |           | not null | nextval('all_average_id_seq'::regclass) | plain    |              |
 host_id       | bigint                   |           |          |                                         | plain    |              |
 organizer     | character varying(64)    |           | not null |                                         | extended |              |
 members       | character varying(64)    |           | not null |                                         | extended |              |
 aa_type       | character varying(16)    |           | not null | 'normal'::character varying             | extended |              |
 credit        | numeric(7,2)             |           | not null | 0.0                                     | main     |              |
 amount        | numeric(7,2)             |           | not null | 0.0                                     | main     |              |
 aa_number     | smallint                 |           | not null |                                         | plain    |              |
 paid_number   | smallint                 |           | not null | 0                                       | plain    |              |
 aa_content    | character varying(100)   |           | not null | ''::character varying                   | extended |              |
 order_id      | bigint                   |           | not null | 0                                       | plain    |              |
 expire_time   | timestamp with time zone |           | not null |                                         | plain    |              |
 group_chat_id | character varying[]      |           |          |                                         | extended |              |
 create_time   | timestamp with time zone |           | not null | now()                                   | plain    |              |
 update_time   | timestamp with time zone |           | not null | now()                                   | plain    |              |
 status        | smallint
id 自增id
host_id 域id join host_info
organizer 发起者 user@domain
members json.dumps({usera:12,userb:13})
aa_type


"""