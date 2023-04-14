'''
Created by auto_sdk on 2020.01.08
'''
from ..base import RestApi


class AlibabaTradeServiceChargeGetRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.currency = None

    def getapiname(self):
        return 'alibaba.trade.service.charge.get'
