'''
Created by auto_sdk on 2019.11.21
'''
from ..base import RestApi


class AlibabaSellerOrderShippingChannelsRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.param_channel_request = None

    def getapiname(self):
        return 'alibaba.seller.order.shipping.channels'
