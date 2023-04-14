# -*- coding: utf-8 -*-
# @Time    : 2021/2/20 13:32
# @Author  : zhaohui
# @FileName: flask_elasticsearch.py
# @Software: PyCharm

from elasticsearch import Elasticsearch


class FlaskElasticsearch:

    def __init__(self):
        self.es = None

    def init_app(self, app):
        self.es = Elasticsearch(
            hosts=app.config.get('ELASTICSEARCH_HOST'),
            port=app.config.get('ELASTICSEARCH_PORT'),
            http_auth=(app.config.get('ELASTICSEARCH_AUTH_USER'), app.config.get('ELASTICSEARCH_AUTH_PASS')),
            sniff_on_start=app.config.get('ELASTICSEARCH_SNIFF_ON_START'),
            sniff_on_connection_fail=app.config.get('ELASTICSEARCH_SNIFF_ON_CONNECTION_FAIL'),
            sniffer_timeout=app.config.get('ELASTICSEARCH_SNIFFER_TIMEOUT'),
            timeout=60
        )

    def __getattr__(self, item):
        return getattr(self.es, item)
