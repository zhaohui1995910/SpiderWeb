'''
Created by auto_sdk on 2018.11.20
'''
from ..base import RestApi


class AlibabaScbpShowcaseUpdateproductRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.new_product_id = None
        self.window_id = None

    def getapiname(self):
        return 'alibaba.scbp.showcase.updateproduct'
