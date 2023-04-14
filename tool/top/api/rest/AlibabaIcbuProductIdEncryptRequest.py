'''
Created by auto_sdk on 2020.06.17
'''
from ..base import RestApi


class AlibabaIcbuProductIdEncryptRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.language = None
        self.product_id = None

    def getapiname(self):
        return 'alibaba.icbu.product.id.encrypt'
