'''
Created by auto_sdk on 2018.07.26
'''
from ..base import RestApi


class AlibabaIcbuCategoryAttrGetRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.attribute_request = None

    def getapiname(self):
        return 'alibaba.icbu.category.attr.get'
