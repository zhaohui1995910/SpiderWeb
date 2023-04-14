'''
Created by auto_sdk on 2020.04.27
'''
from ..base import RestApi


class AlibabaTradeAddressGetRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.address_request = None

    def getapiname(self):
        return 'alibaba.trade.address.get'
