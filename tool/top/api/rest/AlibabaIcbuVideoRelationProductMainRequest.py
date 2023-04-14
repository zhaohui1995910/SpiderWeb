'''
Created by auto_sdk on 2020.05.28
'''
from ..base import RestApi


class AlibabaIcbuVideoRelationProductMainRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.product_id = None
        self.video_id = None

    def getapiname(self):
        return 'alibaba.icbu.video.relation.product.main'
