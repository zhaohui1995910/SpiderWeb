'''
Created by auto_sdk on 2021.08.18
'''
from ..base import RestApi


class AlibabaIcbuProductGroupGetRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.extra_context = None
        self.group_id = None

    def getapiname(self):
        return 'alibaba.icbu.product.group.get'
