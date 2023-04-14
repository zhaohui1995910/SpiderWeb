'''
Created by auto_sdk on 2020.04.28
'''
from ..base import RestApi


class AlibabaSellerOrderShippingRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.shipping_request = None

    def getapiname(self):
        return 'alibaba.seller.order.shipping'
