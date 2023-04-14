'''
Created by auto_sdk on 2020.04.14
'''
from ..base import RestApi


class AlibabaTradeOrderModifyRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.param_order_modify = None

    def getapiname(self):
        return 'alibaba.trade.order.modify'
