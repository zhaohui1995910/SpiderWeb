'''
Created by auto_sdk on 2020.10.20
'''
from ..base import RestApi


class AlibabaIcbuEcologyWriteRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.symbol = None

    def getapiname(self):
        return 'alibaba.icbu.ecology.write'
