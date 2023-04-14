'''
Created by auto_sdk on 2020.08.07
'''
from ..base import RestApi


class AlibabaOrderTradeTtGetRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.e_trade_id = None

    def getapiname(self):
        return 'alibaba.order.trade.tt.get'
