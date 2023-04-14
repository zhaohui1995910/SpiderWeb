'''
Created by auto_sdk on 2018.10.31
'''
from ..base import RestApi


class AlibabaProcurementMysupplierListRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.current_page = None
        self.page_size = None
        self.type = None

    def getapiname(self):
        return 'alibaba.procurement.mysupplier.list'
