'''
Created by auto_sdk on 2020.10.13
'''
from ..base import RestApi


class AlibabaIcbuCategorySchemaLevelGetRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.cat_id = None
        self.language = None
        self.xml = None

    def getapiname(self):
        return 'alibaba.icbu.category.schema.level.get'
