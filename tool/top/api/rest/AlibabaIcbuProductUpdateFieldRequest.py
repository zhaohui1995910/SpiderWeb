'''
Created by auto_sdk on 2020.04.30
'''
from ..base import RestApi


class AlibabaIcbuProductUpdateFieldRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.attributes = None
        self.bulk_discount_prices = None
        self.category_id = None
        self.custom_info = None
        self.description = None
        self.extra_context = None
        self.group_id = None
        self.is_smart_edit = None
        self.keywords = None
        self.language = None
        self.main_image = None
        self.market = None
        self.product_id = None
        self.product_sku = None
        self.product_type = None
        self.sourcing_trade = None
        self.subject = None
        self.use_sku_price = None
        self.wholesale_trade = None

    def getapiname(self):
        return 'alibaba.icbu.product.update.field'
