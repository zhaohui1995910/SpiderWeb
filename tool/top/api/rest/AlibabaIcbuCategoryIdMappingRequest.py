'''
Created by auto_sdk on 2020.10.10
'''
from ..base import RestApi


class AlibabaIcbuCategoryIdMappingRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.attribute_id = None
        self.attribute_value_id = None
        self.cat_id = None
        self.convert_type = None

    def getapiname(self):
        return 'alibaba.icbu.category.id.mapping'
