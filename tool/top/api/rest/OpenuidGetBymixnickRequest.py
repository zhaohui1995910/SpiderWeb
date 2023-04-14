'''
Created by auto_sdk on 2021.08.20
'''
from ..base import RestApi


class OpenuidGetBymixnickRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.mix_nick = None

    def getapiname(self):
        return 'taobao.openuid.get.bymixnick'
