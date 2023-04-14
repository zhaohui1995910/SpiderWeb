'''
Created by auto_sdk on 2019.09.23
'''
from ..base import RestApi


class AlibabaIcbuProductBatchUpdateDisplayRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.new_display = None
        self.product_id_list = None

    def getapiname(self):
        return 'alibaba.icbu.product.batch.update.display'
