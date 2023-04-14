'''
Created by auto_sdk on 2020.05.08
'''
from ..base import RestApi


class AlibabaIcbuPhotobankListRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.current_page = None
        self.extra_context = None
        self.group_id = None
        self.location_type = None
        self.page_size = None

    def getapiname(self):
        return 'alibaba.icbu.photobank.list'
