'''
Created by auto_sdk on 2021.07.19
'''
from ..base import RestApi


class AlibabaIcbuProductListRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.category_id = None
        self.current_page = None
        self.gmt_modified_from = None
        self.gmt_modified_to = None
        self.group_id1 = None
        self.group_id2 = None
        self.group_id3 = None
        self.id = None
        self.language = None
        self.page_size = None
        self.subject = None

    def getapiname(self):
        return 'alibaba.icbu.product.list'
