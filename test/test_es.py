# -*- coding: utf-8 -*-
# @Time    : 2021/2/20 10:30
# @Author  : zhaohui
# @FileName: test_es.py
# @Software: PyCharm


from elasticsearch import Elasticsearch

# ELASTICSEARCH_HOST = ['192.168.123.60', '192.168.123.61', '192.168.123.62', '192.168.123.65']
ELASTICSEARCH_HOST = ['192.168.125.179']
ELASTICSEARCH_POST = 9200
ELASTICSEARCH_AUTH_USER = 'elastic'
ELASTICSEARCH_AUTH_PASS = 'changeme'
ELASTICSEARCH_SNIFF_ON_START = False
ELASTICSEARCH_SNIFF_ON_CONNECTION_FAIL = True
ELASTICSEARCH_SNIFFER_TIMEOUT = None

host = [{'192.168.123.60': 9200}, {'192.168.123.61': 9200}, {'192.168.123.62': 9200}, {'192.168.123.65': 9200}]

es = Elasticsearch(
    hosts=ELASTICSEARCH_HOST,
    port=ELASTICSEARCH_POST,
    http_auth=(ELASTICSEARCH_AUTH_USER, ELASTICSEARCH_AUTH_PASS),
    sniff_on_start=ELASTICSEARCH_SNIFF_ON_START,
    sniff_on_connection_fail=ELASTICSEARCH_SNIFF_ON_CONNECTION_FAIL,
    sniffer_timeout=ELASTICSEARCH_SNIFFER_TIMEOUT,
    maxsize=25
)

# 查询同步下载
body1 = {'query': {'bool': {
    'must': [
        {'match': {'app': 'lumibox'}},
        {'term': {'action.keyword': {'value': '数据/同步上传'}}}
    ]}}}

result1 = es.search(
    index='app-op-log*',
    scroll='10m',
    size=100,
    body=body1
)

id_list = [i['_id'] for i in result1['hits']['hits']]
scroll_id = result1['_scroll_id']

update_body1 = {'query': {'ids': {'values': id_list}}, 'script': {'source': 'ctx._source["action"]="待处理"'}}
es.update_by_query(index='app-op-log*', body=update_body1)

i = 1
# 1.1 继续通过游标查询（scroll_id)查询
while True:
    print(i + 1)
    result = es.scroll(scroll_id=scroll_id, scroll='10m')
    _id_list = [i['_id'] for i in result1['hits']['hits']]

    if len(_id_list) != 0:
        _update_body = {'query': {'ids': {'values': _id_list}}, 'script': {'source': 'ctx._source["action"]="待处理"'}}
        es.update_by_query(index='app-op-log*', body=_update_body)

    if len(_id_list) < 100:
        _update_body = {'query': {'ids': {'values': _id_list}}, 'script': {'source': 'ctx._source["action"]="待处理"'}}
        es.update_by_query(index='app-op-log*', body=_update_body)
        break

# 遍历 更新为 待更新

# 查询同步上传
# 遍历更新为 数据/同步下载

# 查询 待更新
# 遍历 更新为 数据/同步上传
