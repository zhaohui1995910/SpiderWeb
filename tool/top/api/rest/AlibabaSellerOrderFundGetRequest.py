'''
Created by auto_sdk on 2021.02.02
'''
from ..base import RestApi


class AlibabaSellerOrderFundGetRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.data_select = None
        self.e_trade_id = None

    def getapiname(self):
        return 'alibaba.seller.order.fund.get'
