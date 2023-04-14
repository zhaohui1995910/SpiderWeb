'''
Created by auto_sdk on 2020.10.13
'''
from ..base import RestApi


class AlibabaIcbuProductSchemaAddRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.param_product_top_publish_request = None

    def getapiname(self):
        return 'alibaba.icbu.product.schema.add'
