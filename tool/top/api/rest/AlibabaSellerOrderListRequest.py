'''
Created by auto_sdk on 2020.03.25
'''
from ..base import RestApi


class AlibabaSellerOrderListRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.param_trade_ecology_order_list_query = None

    def getapiname(self):
        return 'alibaba.seller.order.list'
