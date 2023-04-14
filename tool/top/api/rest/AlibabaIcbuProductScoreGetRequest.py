'''
Created by auto_sdk on 2020.07.02
'''
from ..base import RestApi


class AlibabaIcbuProductScoreGetRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.product_id = None

    def getapiname(self):
        return 'alibaba.icbu.product.score.get'
