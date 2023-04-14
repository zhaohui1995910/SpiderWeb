'''
Created by auto_sdk on 2021.08.18
'''
from ..base import RestApi


class AlibabaSellerOrderLogisticsGetRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.data_select = None
        self.e_trade_id = None

    def getapiname(self):
        return 'alibaba.seller.order.logistics.get'
