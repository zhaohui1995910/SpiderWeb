'''
Created by auto_sdk on 2019.12.12
'''
from ..base import RestApi


class AlibabaIcbuCategoryAttrvalueGetRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.attribute_value_request = None

    def getapiname(self):
        return 'alibaba.icbu.category.attrvalue.get'
