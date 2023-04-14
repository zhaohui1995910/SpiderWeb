'''
Created by auto_sdk on 2018.11.20
'''
from ..base import RestApi


class AlibabaIcbuPhotobankGroupListRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.extra_context = None
        self.id = None

    def getapiname(self):
        return 'alibaba.icbu.photobank.group.list'
