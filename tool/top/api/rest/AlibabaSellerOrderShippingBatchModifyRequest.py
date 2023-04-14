'''
Created by auto_sdk on 2020.05.08
'''
from ..base import RestApi


class AlibabaSellerOrderShippingBatchModifyRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.param_one_batch_modify_request = None

    def getapiname(self):
        return 'alibaba.seller.order.shipping.batch.modify'
