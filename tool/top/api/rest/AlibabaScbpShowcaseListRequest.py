'''
Created by auto_sdk on 2018.11.20
'''
from ..base import RestApi


class AlibabaScbpShowcaseListRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.per_page_size = None
        self.to_page = None

    def getapiname(self):
        return 'alibaba.scbp.showcase.list'
