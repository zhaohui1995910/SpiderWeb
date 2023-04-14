'''
Created by auto_sdk on 2021.01.06
'''
from ..base import RestApi


class AlibabaIcbuPhotobankUploadRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.extra_context = None
        self.file_name = None
        self.group_id = None
        self.image_bytes = None

    def getapiname(self):
        return 'alibaba.icbu.photobank.upload'

    def getMultipartParas(self):
        return ['image_bytes']
