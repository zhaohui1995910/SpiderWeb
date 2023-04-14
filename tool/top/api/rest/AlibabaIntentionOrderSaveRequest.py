'''
Created by auto_sdk on 2020.12.21
'''
from ..base import RestApi


class AlibabaIntentionOrderSaveRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.intention_order = None

    def getapiname(self):
        return 'alibaba.intention.order.save'
