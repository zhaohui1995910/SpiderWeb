'''
Created by auto_sdk on 2020.07.06
'''
from ..base import RestApi


class AlibabaIcbuCategoryPostcatGetRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.post_cat_request = None

    def getapiname(self):
        return 'alibaba.icbu.category.postcat.get'
