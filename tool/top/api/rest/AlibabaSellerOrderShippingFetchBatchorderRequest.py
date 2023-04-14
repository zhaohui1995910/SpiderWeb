'''
Created by auto_sdk on 2019.12.31
'''
from ..base import RestApi


class AlibabaSellerOrderShippingFetchBatchorderRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.param_batch_order_request = None

    def getapiname(self):
        return 'alibaba.seller.order.shipping.fetch.batchorder'
