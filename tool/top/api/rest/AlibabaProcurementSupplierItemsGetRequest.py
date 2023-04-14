'''
Created by auto_sdk on 2018.10.31
'''
from ..base import RestApi


class AlibabaProcurementSupplierItemsGetRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.product_list_query = None

    def getapiname(self):
        return 'alibaba.procurement.supplier.items.get'
