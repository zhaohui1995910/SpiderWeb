'''
Created by auto_sdk on 2020.04.28
'''
from ..base import RestApi


class AlibabaOrderPictureUploadRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.data = None
        self.param_file_upload_request = None

    def getapiname(self):
        return 'alibaba.order.picture.upload'

    def getMultipartParas(self):
        return ['data']
