'''
Created by auto_sdk on 2020.02.27
'''
from ..base import RestApi


class AlibabaIcbuCategoryLevelAttrGetRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.attribute_value_request = None

    def getapiname(self):
        return 'alibaba.icbu.category.level.attr.get'
