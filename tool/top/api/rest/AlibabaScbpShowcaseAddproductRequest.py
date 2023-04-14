'''
Created by auto_sdk on 2018.11.20
'''
from ..base import RestApi


class AlibabaScbpShowcaseAddproductRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.product_id_list = None

    def getapiname(self):
        return 'alibaba.scbp.showcase.addproduct'
