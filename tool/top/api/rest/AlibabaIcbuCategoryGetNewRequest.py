'''
Created by auto_sdk on 2020.12.16
'''
from ..base import RestApi


class AlibabaIcbuCategoryGetNewRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.cat_id = None

    def getapiname(self):
        return 'alibaba.icbu.category.get.new'
