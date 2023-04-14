'''
Created by auto_sdk on 2019.07.08
'''
from ..base import RestApi


class AlibabaIcbuPhotobankGroupOperateRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.photo_group_operation_request = None

    def getapiname(self):
        return 'alibaba.icbu.photobank.group.operate'
