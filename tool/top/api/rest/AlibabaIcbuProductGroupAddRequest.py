'''
Created by auto_sdk on 2018.07.26
'''
from ..base import RestApi


class AlibabaIcbuProductGroupAddRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.extra_context = None
        self.group_name = None
        self.parent_id = None

    def getapiname(self):
        return 'alibaba.icbu.product.group.add'
