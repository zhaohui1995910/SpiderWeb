'''
Created by auto_sdk on 2020.05.07
'''
from ..base import RestApi


class AlibabaSellerOrderMultiShippingRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.param_multi_shipping_create_request = None

    def getapiname(self):
        return 'alibaba.seller.order.multi.shipping'
