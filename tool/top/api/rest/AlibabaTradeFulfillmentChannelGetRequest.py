'''
Created by auto_sdk on 2020.01.08
'''
from ..base import RestApi


class AlibabaTradeFulfillmentChannelGetRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.language = None

    def getapiname(self):
        return 'alibaba.trade.fulfillment.channel.get'
