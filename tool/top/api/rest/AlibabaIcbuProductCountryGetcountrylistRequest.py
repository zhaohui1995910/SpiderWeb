'''
Created by auto_sdk on 2021.09.26
'''
from ..base import RestApi


class AlibabaIcbuProductCountryGetcountrylistRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.country_request = None

    def getapiname(self):
        return 'alibaba.icbu.product.country.getcountrylist'
