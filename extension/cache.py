# -*- coding: utf-8 -*-
# @Time    : 2021/6/10 9:02
# @Author  : 10867
# @FileName: cache.py
# @Software: PyCharm
from flask_caching import Cache

cache = Cache()


def init_cache(app):
    cache.init_app(app=app)
    return cache
