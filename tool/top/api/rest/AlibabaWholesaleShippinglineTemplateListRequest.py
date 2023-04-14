'''
Created by auto_sdk on 2018.07.26
'''
from ..base import RestApi


class AlibabaWholesaleShippinglineTemplateListRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.count = None
        self.page_num = None

    def getapiname(self):
        return 'alibaba.wholesale.shippingline.template.list'
