'''
Created by auto_sdk on 2020.05.28
'''
from ..base import RestApi


class AlibabaIcbuVideoQueryRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.current_page = None
        self.page_size = None

    def getapiname(self):
        return 'alibaba.icbu.video.query'
