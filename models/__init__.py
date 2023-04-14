from dataclasses import asdict
from uuid import uuid1

from flask_pymongo import PyMongo

from tool.flask_elasticsearch import FlaskElasticsearch

lumi_es = FlaskElasticsearch()
local_mongo = PyMongo(connect=False)
spider_mongo = PyMongo(connect=False)


def init_app(app):
    """初始化配置"""
    local_mongo.init_app(app, uri=app.config.get('LOCAL_MONGO_URL'), connect=False)
    spider_mongo.init_app(app, uri=app.config.get('SPIDER_MONGO_URL'), connect=False)
    lumi_es.init_app(app)


class BaseMethod:
    def to_json(self):
        _dict = self.__dict__
        if "_sa_instance_state" in _dict:
            del _dict["_sa_instance_state"]
        return _dict


# noinspection PyDataclass,PyAttributeOutsideInit
class BaseMongoModels:

    @staticmethod
    def find(collection, conditions):
        '''查询'''
        db = local_mongo.cx['spider_web']
        collection = getattr(db, collection)
        return list(collection.find(filter=conditions))

    def insert(self, collection):
        '''新增'''
        self._id = uuid1().hex
        db = local_mongo.cx['spider_web']
        collection = getattr(db, collection)
        collection.insert_one(asdict(self))
