'''
Created by auto_sdk on 2020.05.08
'''
from ..base import RestApi


class AlibabaSellerOrderShippingorderQueryRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.param_trade_ecology_order_request = None

    def getapiname(self):
        return 'alibaba.seller.order.shippingorder.query'
