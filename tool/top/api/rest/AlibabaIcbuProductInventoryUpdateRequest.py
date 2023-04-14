'''
Created by auto_sdk on 2020.11.23
'''
from ..base import RestApi


class AlibabaIcbuProductInventoryUpdateRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.request_param = None

    def getapiname(self):
        return 'alibaba.icbu.product.inventory.update'
