'''
Created by auto_sdk on 2020.06.01
'''
from ..base import RestApi


class AlibabaIcbuVideoUploadRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.cover_url = None
        self.video_name = None
        self.video_path = None

    def getapiname(self):
        return 'alibaba.icbu.video.upload'
