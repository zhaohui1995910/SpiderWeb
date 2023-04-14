'''
Created by auto_sdk on 2020.12.14
'''
from ..base import RestApi


class AlibabaSellerAddressSaveRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.param_trade_ecology_address_save_request = None

    def getapiname(self):
        return 'alibaba.seller.address.save'
