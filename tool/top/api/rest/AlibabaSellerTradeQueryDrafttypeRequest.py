'''
Created by auto_sdk on 2020.12.14
'''
from ..base import RestApi


class AlibabaSellerTradeQueryDrafttypeRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)

    def getapiname(self):
        return 'alibaba.seller.trade.query.drafttype'
