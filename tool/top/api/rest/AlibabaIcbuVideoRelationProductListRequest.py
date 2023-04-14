'''
Created by auto_sdk on 2020.06.29
'''
from ..base import RestApi


class AlibabaIcbuVideoRelationProductListRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.type = None
        self.video_id = None

    def getapiname(self):
        return 'alibaba.icbu.video.relation.product.list'
