'''
Created by auto_sdk on 2021.09.02
'''
from ..base import RestApi


class AlibabaSellerOrderGetRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.data_select = None
        self.e_trade_id = None
        self.language = None

    def getapiname(self):
        return 'alibaba.seller.order.get'
