import io
import re
import uuid
import json
from functools import wraps
from hashlib import sha1
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timedelta

import pandas as pd
import pymongo
import pymssql
import requests
from bson.objectid import ObjectId
from dateutil.parser import parse as date_parse
from flask import current_app, jsonify, request, send_file
from flask_restful import Resource, fields, marshal, reqparse
from jsonpath import jsonpath
from pymongo import ASCENDING, DESCENDING

from models import lumi_es, spider_mongo, local_mongo
from models.spider import CSARelation
from extension.cache import cache
from tool.flask_pymssql import DBConnection


# Amazon数据展示Api

# noinspection PyMethodMayBeStatic
class AamzonItemMinix:

    def set_reviews_fields(self, item):
        """item添加评论表中的字段"""
        db = spider_mongo.cx['amazon_spider']
        collection_name = '%s_product_reviews' % item['brand']
        collection = getattr(db, collection_name)

        totle = collection.find({'productId': item['asin']}).count()
        item['reviewCount'] = totle

        negative_count = collection.find({'productId': item['asin'], 'level': {'$lte': '3'}}).count()
        praise_count = collection.find({'productId': item['asin'], 'level': {'$gt': '3'}}).count()
        item['praise_count'], item['negative_count'] = praise_count, negative_count

    def set_info_fields(self, item):
        """item添加INFO表中的字段"""
        db = spider_mongo.cx['amazon_spider']
        collection_name = '%s_product_info' % item['brand']
        collection = getattr(db, collection_name)

        result_item = collection.find_one({'asin': item['asin']}, sort=[('create_datetime', pymongo.DESCENDING)])
        # 添加 库存 字段
        stock = jsonpath(result_item, '$..buyingOptions..availability.type')
        item['stock'] = stock[0] if stock else None
        # 添加 图片地址 字段
        product_images = result_item['productImages']
        image_dict = json.loads(product_images)
        item['image'] = image_dict[0].get('lowRes').get('url') if image_dict else None
        # 添加 标题 字段
        item['info_title'] = result_item['title']
        # 添加 （最高/最低）价 字段
        marke_min_price = jsonpath(result_item, '$..marketplaceOfferSummary..minPrice.amount')
        market_max_price = jsonpath(result_item, '$..marketplaceOfferSummary..maxPrice.amount')

        item['min_price'] = marke_min_price[0] if marke_min_price else None
        item['max_price'] = market_max_price[0] if market_max_price else None

    def set_detail_fields(self, item):
        """item添加详情表中的字段"""
        db = spider_mongo.cx['amazon_spider']
        collection_name = '%s_product_detail' % item['brand']
        collection = getattr(db, collection_name)
        result_item = collection.find_one(
            {'asin': item['asin']}, {'productInfo': 1},
            sort=[("spider_datetime", pymongo.DESCENDING)]
        )
        if result_item:
            # 添加 包装尺寸 字段
            item['package_dimensions'] = result_item['productInfo'].get('Package Dimensions') if result_item else None
            # 添加 发布时间 字段
            release_datetime = result_item['productInfo'].get('Date First Available')
            release_datetime = date_parse(release_datetime).strftime('%Y-%m-%d') if release_datetime else None
            item['releaseDatetime'] = release_datetime
            # 添加 产品TOP排名
            best_sellers_rank = result_item['productInfo'].get('Best Sellers Rank')
            if best_sellers_rank:
                most_top_number = None
                if isinstance(best_sellers_rank, dict):
                    for i in best_sellers_rank:
                        a = i.split(' ', 1)
                        if a:
                            b = int(a[0].replace('#', '').replace(',', ''))
                            if most_top_number is None:
                                most_top_number = b
                            elif b < most_top_number:
                                most_top_number = b
                    item['most_top_number'] = most_top_number
                    item['best_sellers_rank'] = '\n'.join(best_sellers_rank.keys())
                else:
                    item['best_sellers_rank'] = best_sellers_rank


class DPGXWH(Resource):
    """店铺关系维护"""
    parser = reqparse.RequestParser()
    result_marshal = {
        'id'          : fields.String(attribute=lambda x: x['_id']),
        'brand_name'  : fields.String,
        'brand_source': fields.String,
        'customer_id' : fields.Integer
    }

    def get(self):

        page = int(request.args.get('page', 1))
        if page <= 0:
            return jsonify({'code': 50000, 'data': 'page 必须大于0'})

        limit = int(request.args.get('limit', 15))

        db = local_mongo.cx['spider_web']
        find_result = db.customer_brand_relation.find({}, {'create_date': 0})
        count = find_result.count()
        find_result.limit(limit).skip((page - 1) * limit)

        result = [i for i in find_result]
        result = marshal(result, self.result_marshal)

        return jsonify({'code': 20000, 'data': {'item_list': result, 'item_count': count}})

    def post(self):
        """新增数据"""
        self.parser.add_argument('customer_id', type=int, default="", location='json', help='验证错误')
        self.parser.add_argument('brand_name', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('brand_source', type=str, default="", location='json', help='验证错误')
        args = self.parser.parse_args()

        data = CSARelation(
            customer_id=args.get('customer_id'),
            brand_name=args.get('brand_name'),
            brand_source=args.get('brand_source'),
            create_date=datetime.now()
        )

        db = local_mongo.cx['spider_web']
        if db.customer_brand_relation.find_one({
            'customer_id' : data.customer_id,
            'brand_name'  : data.brand_name,
            'brand_source': data.brand_source
        }):
            return jsonify({'code': 20001, 'data': '数据已存在'})

        db.customer_brand_relation.insert_one(asdict(data))

        return jsonify({'code': 20000, 'data': 'ok'})

    def put(self):
        """修改数据"""
        self.parser.add_argument('id', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('customer_id', type=int, default="", location='json', help='验证错误')
        self.parser.add_argument('brand_name', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('brand_source', type=str, default="", location='json', help='验证错误')
        args = self.parser.parse_args()

        _id = ObjectId(args.get('id'))
        db = local_mongo.cx['spider_web']
        item = db.customer_brand_relation.find_one({'_id': _id})
        if not item:
            return jsonify({'code': 50000, 'data': '数据不存在，无法修改'})

        update_dict = {
            'customer_id' : args.get('customer_id'),
            'brand_name'  : args.get('brand_name'),
            'brand_source': args.get('brand_source'),
        }

        db.customer_brand_relation.update_one(
            {'_id': _id},
            {
                '$set': update_dict
            }
        )
        return jsonify({'code': 20000, 'data': '数据已更新'})

    def delete(self):
        self.parser.add_argument('id', type=str, default="", location='json', help='验证错误')
        args = self.parser.parse_args()

        db = local_mongo.cx['spider_web']
        db.customer_brand_relation.delete_one(
            {'_id': ObjectId(args.get('id'))}
        )

        return jsonify({'code': 20000, 'data': '删除成功'})


class AmazonPLPM(Resource, AamzonItemMinix):
    """amazon 品类排名"""

    result_marshal = {
        'asin'          : fields.String,
        'createDate'    : fields.DateTime,
        'department'    : fields.String,
        'departmentLink': fields.String(attribute='department_link'),
        'imgLink'       : fields.String,
        'negative_count': fields.Integer,
        'praise_count'  : fields.Integer,
        'number'        : fields.Integer,
        'productUrl'    : fields.String,
        'level'         : fields.Float(attribute='reviewScores'),
        'title'         : fields.String,
        'stock'         : fields.String(default=None),
        'price'         : fields.String,
        'brand'         : fields.String,
        'dimensions'    : fields.String(attribute='package_dimensions')
    }
    limit = 15
    parser = reqparse.RequestParser()

    def post(self):

        self.parser.add_argument('page', type=int, default=1, location='json', help='验证错误')
        self.parser.add_argument('vesa', type=list, default=[], location='json', help='验证错误')
        self.parser.add_argument('category', type=list, default=[], location='json', help='验证错误')
        self.parser.add_argument('isnew', type=str, default=[], location='json', help='验证错误')

        args = self.parser.parse_args()

        filter_dict = dict()
        if args.get('vesa'):
            filter_dict['vesa'] = {'$in': args.get('vesa')}

        if args.get('category'):
            filter_dict['department'] = {'$in': args.get('category')}

        total = 100 * len(args.get('category')) if args.get('category') else 100

        # if args.get('isnew'):
        #     filter_dict['isnew'] = args.get('isnew')
        db = spider_mongo.cx['amazon_spider']
        collection = db.amazon_best_sellers
        find_result = collection.find(
            filter_dict, {'_id': 0},
            sort=[('createDate', DESCENDING), ('number', ASCENDING)]
        ).skip(self.limit * (int(args.get('page')) - 1)).limit(self.limit)
        result = [i for i in find_result]

        # 添加brand字段
        # [self.set_brand_field(i) for i in result]

        # futures thread版
        with ThreadPoolExecutor(max_workers=self.limit) as executor_pool:
            executor_pool.map(self.set_brand_field, result)
            executor_pool.map(self.set_department_field, result)
            executor_pool.map(self.set_info_fields, result)
            executor_pool.map(self.set_detail_fields, result)
            executor_pool.map(self.set_reviews_fields, result)

        return jsonify({'code' : 20000,
                        'data' : marshal(result, self.result_marshal),
                        'total': total})

    # noinspection PyMethodMayBeStatic
    def set_brand_field(self, item):
        """添加brand字段"""
        db = spider_mongo.cx['amazon_spider']
        result = db.amazon_product_set.find_one({'asin': item['asin']})
        item.setdefault('brand', result['brand']) if result else None

    # noinspection PyMethodMayBeStatic
    def set_department_field(self, item):
        """添加top品类链接字段"""
        db = spider_mongo.cx['amazon_spider']
        department = db.amazon_department_set.find_one({'department': item['department']})
        item.setdefault('department_link', department['link']) if department else None


class AmazonProductInfo(Resource, AamzonItemMinix):
    """amazon 商品列表"""
    limit = 15
    parser = reqparse.RequestParser()
    result_marshal = {
        'brand'          : fields.String,
        'image'          : fields.String,
        'asin'           : fields.String,
        'url'            : fields.String,
        'title'          : fields.String,
        'stock'          : fields.String,
        'rating'         : fields.String(attribute='level'),

        'reviewCount'    : fields.String,
        'praise_count'   : fields.String,
        'negative_count' : fields.String,
        'goodReviewRate' : fields.String,
        'badReviewRate'  : fields.String,

        'price'          : fields.String,
        'marketMinPrice' : fields.String(attribute='min_price'),
        'marketMaxPrice' : fields.String(attribute='max_price'),

        'dimensions'     : fields.String(attribute='package_dimensions'),
        'release_date'   : fields.String(attribute='releaseDatetime'),
        'top'            : fields.String,
        'topCategory'    : fields.String,
        'topCategoryUrl' : fields.String,
        'mostTopNumber'  : fields.String(attribute='most_top_number'),
        'bestSellersRank': fields.String(attribute='best_sellers_rank')
    }

    def post(self):
        self.parser.add_argument('page', type=int, default=1, location='json', help='验证错误')
        self.parser.add_argument('category', type=list, location='json', help='验证错误')
        self.parser.add_argument('vesa', type=list, location='json', help='验证错误')
        self.parser.add_argument('brands', type=list, location='json', help='验证错误')
        self.parser.add_argument('isnew', type=int, location='json', help='验证错误')
        args = self.parser.parse_args()

        # 多品牌
        # with ThreadPoolExecutor(max_workers=5) as executor:
        #     for brand in args.get('brands'):
        #         find_result.extend(executor.submit(self.get_product_list, brand).result())

        # 单品牌
        # find_result.extend(self.get_product_list(args.get('brand'), args.get('page')))
        # 给字典添加brand字段
        # [d.setdefault('brand', args.get('brand')) for d in find_result]

        filter_dict = {
            'brand'      : {'$in': args.get('brands')},
            'isExistInfo': True
        }
        if args.get('category'):
            filter_dict['top_category'] = {'$in': args.get('category')}

        # 添加 是否新品 条件过滤
        if args.get('isnew'):
            filter_dict['topCategory'] = {'$gte': datetime.now() - timedelta(days=30)}

        # 添加 MAx.vesa 条件过滤
        if args.get('vesa'):
            filter_dict['$or'] = [{'content': {'$regex': i}} for i in args.get('vesa')]

        db = spider_mongo.cx['amazon_spider']
        find_result = db.amazon_product_set.find(
            filter_dict,
            {'_id': 0},
            sort=[('brand', 1), ('releaseDatetime', -1)]
        ).skip(self.limit * (args.get('page') - 1)).limit(self.limit)
        find_result = list(find_result)

        find_total = db.amazon_product_set.find(
            filter_dict,
            {'_id': 0},
            sort=[('brand', 1), ('releaseDatetime', -1)]
        ).count()

        with ThreadPoolExecutor(max_workers=self.limit) as executor:
            executor.map(self.set_detail_fields, find_result)
            executor.map(self.set_info_fields, find_result)
            executor.map(self.set_reviews_fields, find_result)

        return jsonify({
            'code' : 20000,
            'data' : marshal(find_result, self.result_marshal),
            'total': find_total
        })

    def get_product_list(self, brand: str, page):
        """获取品牌商品"""
        db = spider_mongo.cx['amazon_spider']
        collection_name = '%s_product_list' % brand
        collection = getattr(db, collection_name)
        r = collection.find({}, sort=[('spiderDatetime', -1)]).skip(self.limit * (page - 1)).limit(self.limit)

        return [i for i in r]


class AmazonProductReview(Resource):
    result_marshal = {
        'brandName'  : fields.String,
        'productId'  : fields.String,
        'createDate' : fields.String,
        'titleLink'  : fields.String,
        'title'      : fields.String,
        'reviewVp'   : fields.String,
        'authorName' : fields.String,
        'level'      : fields.String,
        'content'    : fields.String,
        'reviewStrip': fields.String,
    }
    limit = 15
    parser = reqparse.RequestParser()

    def get(self):
        self.parser.add_argument('page', type=int, default=1, location='values', help='验证错误')
        self.parser.add_argument('brand', type=str, default=False, location='values', help='验证错误')
        self.parser.add_argument('asin', type=str, default='', location='values', help='验证错误')

        args = self.parser.parse_args()

        collection_name = '%s_product_reviews' % args.get('brand')
        if collection_name[0] == '_':
            return jsonify({'code': 20000, 'data': '请传递正确的参数'})

        db = spider_mongo.cx['amazon_spider']
        collection = getattr(db, collection_name)
        find_result = collection.find(
            {'productId': args.get('asin'), 'level': {'$lte': '3'}},
            sort=[('createDate', -1)]
        )
        find_result.skip(self.limit * (int(args.get('page')) - 1)).limit(self.limit)

        result = [i for i in find_result]

        return jsonify({'code': 20000, 'data': marshal(result, self.result_marshal)})


class AmazonProductHistory(Resource):
    """获取180天的商品价格列表"""

    def get(self):
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not (start_date or end_date):
            _today = datetime.now()
            start_date = (_today - timedelta(days=180)).strftime('%Y-%m-%d')
            end_date = _today.strftime('%Y-%m-%d')

        date_list = pd.date_range(start=start_date, end=end_date)
        x_axis = [d.strftime('%m/%d') for d in date_list]

        brand = request.args.get('brand')
        asin = request.args.get('asin')

        db = spider_mongo.cx['amazon_spider']
        collection_name = '%s_product_list' % brand
        collection = getattr(db, collection_name)

        find_list = collection.find(
            {
                'asin'          : asin,
                'spiderDatetime': {'$gte': start_date, '$lte': end_date}
            }, {'price': 1, 'reviewCount': 1},
            sort=[('spiderDatetime', -1)]).limit(len(x_axis))

        find_list = [i for i in find_list]

        price_list = [i['price'] for i in find_list][::-1]
        review_list = [i['reviewCount'] for i in find_list][::-1]

        result = {'price_list': price_list, 'review_list': review_list, 'x_axis': x_axis}

        return jsonify({'code'      : 20000,
                        'data'      : result,
                        'start_date': start_date,
                        'end_date'  : end_date})


class AmazonClientBrands(Resource):

    def get(self):
        """根据客户的品牌列表"""
        qcbm = request.args.get('qcbm')  # 客户编码
        user_code = request.args.get('userCode')  # 用户id

        # 判断用户是否有客户权限
        customer_permission_api = current_app.config.get('CUSTOMER_PERMISSION')
        body = {
            'qcbm'    : qcbm,
            'userCode': user_code
        }
        response = requests.post(customer_permission_api, json=body)

        if not response.json().get('result'):
            return jsonify({'code': 50000, 'message': '您还没有当前客户权限'})

        db = local_mongo.cx['spider_web']
        result = db.customer_brand_relation.find({'customer_id': int(qcbm)})
        brands = [r.get('brand_name') for r in result]

        return jsonify({'code': 20000, 'data': brands})


class AmazonSearch(Resource):
    """亚马逊关键词查询"""
    parser = reqparse.RequestParser()
    limit = 14

    result_marshal = {
        'id'                  : fields.String(attribute='_id'),
        'asin'                : fields.String,
        'link'                : fields.String(attribute=lambda x: 'https://www.amazon.com/dp/%s' % x['asin']),
        'title'               : fields.String,
        # 'content'           : fields.String(attribute=lambda x: '\n'.join([str(i) for i in x.get('content', [])])),
        'price'               : fields.String,
        'image'               : fields.String,
        'color'               : fields.String(attribute=lambda x: x.get('productInfo').get('Color')),
        'materail'            : fields.String,
        # 'productInfo'       : fields.String(attribute=lambda x: json.dumps(x['productInfo'])),
        'questionsNum'        : fields.String,
        # 'reviewsAnalysis'   : fields.Nested({
        #     'reviewsCount' : fields.String,
        #     'reviewsResult': fields.String,
        # }),
        'reviewsCount'        : fields.String(attribute=lambda x: x.get('reviewsAnalysis', {}).get('reviewsCount')),
        'reviews_result'      : fields.String,
        'sotck'               : fields.String,
        'product_dimensions'  : fields.String(
            attribute=lambda x: x.get('productInfo', {}).get('Product Dimensions', '')
        ),
        'brand'               : fields.String(attribute=lambda x: x.get('productInfo', {}).get('Brand', '')),
        'weight'              : fields.String(attribute=lambda x: x.get('productInfo', {}).get('Item Weight', '')),
        'data_first_available': fields.String(
            attribute=lambda x: date_parse(
                x['productInfo']['Date First Available'].replace('\u200e', '')
            ) if x.get('productInfo', {}).get('Date First Available') else ''
        ),
    }

    def get(self):
        """查询"""
        self.parser.add_argument('keyword', type=str, default='', location='values', help='验证错误')
        self.parser.add_argument('page', type=int, default=1, location='values', help='验证错误')
        self.parser.add_argument('sort', type=str, default=None, location='values', help='验证错误')
        args = self.parser.parse_args()

        sort = []
        if args.get('sort'):
            sort_json = json.loads(args.get('sort'))
            order = sort_json.get('order')
            if order:
                if 'asc' in order:
                    order = pymongo.ASCENDING
                elif 'desc' in order:
                    order = pymongo.DESCENDING
                sort.append((sort_json.get('name'), order))

        find_filter = {'keyword': args.get('keyword')}

        db = spider_mongo.cx['amazon_spider']
        total = db.amazon_search.find(find_filter).count()

        find_result = db.amazon_search.find(
            find_filter,
            sort=sort
        ).skip(self.limit * (int(args.get('page')) - 1)).limit(self.limit)
        item_list = [i for i in find_result]

        with ThreadPoolExecutor(max_workers=self.limit) as executor_pool:
            executor_pool.map(self.parse_materail, item_list)

        result = marshal(item_list, self.result_marshal)

        return jsonify({'code': 20000, 'data': result, 'total': total})

    def delete(self):
        """删除"""
        self.parser.add_argument('asin_list', type=list, default=[], location='json', help='验证错误')
        args = self.parser.parse_args()

        db = spider_mongo.cx['amazon_spider']
        db.amazon_search.delete_many({'asin': {'$in': args.get('asin_list')}})

        return jsonify({'code': 20000, 'data': 'ok'})

    def post(self):
        """下载"""
        self.parser.add_argument('keyword', type=str, default='', location='json', help='验证错误')
        args = self.parser.parse_args()

        db = spider_mongo.cx['amazon_spider']
        result = db.amazon_search.find(
            {'keyword': args.get('keyword')},
            {'_id': 0}
        )
        result = [i for i in result]
        result = marshal(result, self.result_marshal)
        df = pd.DataFrame(data=result)
        # 3 构建excel数据
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer)
        writer.save()
        output.seek(0)

        return send_file(
            output,
            attachment_filename='%s.xlsx' % args.get('keyword'),
            as_attachment=True,
            mimetype='text/csv/xlsx'
        )

    def parse_materail(self, item):
        """
        解析材料字段
        从产品参数中提取包含materail字段
        从产品简介中提取materail关键词前后5个单词
        """
        product_info = item.get('productInfo', {})

        # 从产品参数中提取
        for key in product_info:
            if 'materail' in key.lower():
                item['materail'] = product_info[key]

        # 从产品简介中提取
        if not item.get('materail'):
            content: list = item.get('content')

            for i in content:
                materail_lower = i.lower()
                if 'materail' in materail_lower:
                    materail_list = materail_lower.split()
                    m_index = materail_list.index('materail')
                    # 前5个元素索引
                    q_index = m_index - 5 if m_index - 5 >= 0 else 0
                    # 后5个元素索引
                    h_index = m_index + 5
                    # 拼接
                    materail = materail_list[q_index:m_index] + 'materail' + materail_list[m_index: h_index]
                    item['materail'] = materail


# Tapd考核统计Api

class TapdStat(Resource):
    """获取tapd统计结果"""
    parser = reqparse.RequestParser()
    result_marshal = {
        'name'           : fields.String,
        'bug_score'      : fields.Float(default=7.0),
        'task_score'     : fields.Float,
        'timesheet_score': fields.Float,
        'iteration_score': fields.Float,
        'stat_date'      : fields.String
    }

    def get(self):
        self.parser.add_argument('stat_date', type=str, required=True, location='values', help='验证错误')
        args = self.parser.parse_args()

        db = local_mongo.cx['spider_mongo']
        find_result = list(db.tapd_stat.find(args))
        result = marshal(find_result, self.result_marshal)

        return jsonify({'code': 20000, 'data': result})


class TapdStatDetail(Resource):
    """获取tapd统计详情"""
    parser = reqparse.RequestParser()
    result_marshal = {
        'name'           : fields.String,
        'type'           : fields.String,
        'second_type'    : fields.String,
        'tapd_id'        : fields.String,
        'tapd_name'      : fields.String,
        'exceed'         : fields.Boolean,
        'stat_date'      : fields.String,
        'number'         : fields.Float,
        'update_datetime': fields.DateTime
    }

    def get(self):
        self.parser.add_argument('name', type=str, required=True, location='values', help='验证错误')
        self.parser.add_argument('stat_date', type=str, required=True, location='values', help='验证错误')
        args = self.parser.parse_args()

        db = local_mongo.cx['spider_mongo']
        find_result = list(db.tapd_stat_detail.find(args, {'id': 0}))
        result = marshal(find_result, self.result_marshal)

        return jsonify({'code': 20000, 'data': result})


# 实时汇币Api

class ForeignCurrency(Resource):
    """实时汇币数据"""
    parser = reqparse.RequestParser()
    result_marshal = {
        'id'                  : fields.String(attribute=lambda x: x['_id']),
        'name'                : fields.String,
        'type'                : fields.String,
        'abbreviation'        : fields.String,
        'cash_buy_price'      : fields.String,
        'middle_convert_price': fields.String,
        'spot_buy_price'      : fields.String,
        'spot_sell_price'     : fields.String,
        'release_time'        : fields.String,
        'spider_time'         : fields.String
    }

    pjname_name = {
        '英镑'   : 'GBP',
        '港币'   : 'HKD',
        '美元'   : 'USD',
        '瑞士法郎' : 'CHF',
        '日元'   : 'JPY',
        '加拿大元' : 'CAD',
        '澳大利亚元': 'AUD',
        '欧元'   : 'EUR',
        '澳门元'  : 'MOP'
    }

    def get(self):
        db = spider_mongo.cx['spider']
        self.parser.add_argument('type', type=str, default='中国银行', location='values', help='验证错误')
        args = self.parser.parse_args()

        result = []
        for i, v in self.pjname_name.items():
            item = db.foreign_currency.find_one(
                {'type': args.get('type'), 'name': i},
                sort=[("spider_time", pymongo.DESCENDING)]
            )
            result.append(item)

        return jsonify({'code': 20000, 'data': marshal(result, self.result_marshal)})


# LumiApp日志Api

class LumiAppLogs(Resource):
    """查询LumiApp的操作日志"""
    index = 'app-op-log*'
    page_count = 20
    parser = reqparse.RequestParser()

    result_marshal = {
        'app'             : fields.String,
        'action'          : fields.String,
        'module'          : fields.String,
        'content'         : fields.String,
        'extraInformation': fields.String,
        'operatorInfo'    : fields.Nested({
            'name'       : fields.String,
            'displayName': fields.String,
            'mandator'   : fields.String,
            'factoryName': fields.String,
            'ip'         : fields.String,
            'timeStamp'  : fields.String(attribute=lambda x: date_parse(x['timeStamp']) + timedelta(hours=8)),
        }),
    }

    def validation_params(self) -> dict:
        """验证请求参数"""
        self.parser.add_argument('page', type=int, default=0, location='values', help='验证错误')
        self.parser.add_argument('page_count', type=int, location='values', help='验证错误')
        self.parser.add_argument('start_datetime', type=int, required=True, location='values', help='验证错误')
        self.parser.add_argument('end_datetime', type=int, required=True, location='values', help='验证错误')
        self.parser.add_argument('operatorinfo_name', type=str, location='values', help='验证错误')
        self.parser.add_argument('operatorinfo_displayname', type=str, location='values', help='验证错误')
        self.parser.add_argument('app', type=str, location='values', help='验证错误')
        self.parser.add_argument('action', type=str, location='values', help='验证错误')
        self.parser.add_argument('content', type=str, location='values', help='验证错误')
        self.parser.add_argument('module', type=str, location='values', help='验证错误')
        return self.parser.parse_args()

    def get(self):
        """查询Lumi日志"""
        # 验证请求参数
        args = self.validation_params()
        # 设置每页条数
        self.page_count = args.get('page_count', 20)
        # 构建es查询body
        body = self.build_search_body(args)
        # 查询缓存中total值
        cache_key = sha1(str(body).encode()).hexdigest()
        total = cache.get(cache_key)
        # 如果缓冲中没有值, 再去查询数据库
        if not total:
            count_body = deepcopy(body)
            count_body.pop('sort')
            count_result = lumi_es.count(
                index=self.index,
                body=count_body,
                request_timeout=120
            )
            total: int = count_result['count']
            cache.set(cache_key, total)

        # 查询数据库
        result = lumi_es.search(
            index=self.index,
            size=self.page_count,
            from_=args.get('page') * self.page_count,
            body=body,
            request_timeout=120
        )
        hits = result['hits']['hits']
        data_list = [data['_source'] for data in hits]

        with ThreadPoolExecutor(max_workers=self.page_count) as executor_pool:
            executor_pool.map(LumiAppLogs.parse_content, data_list)

        # 格式化响应
        result = marshal(data_list, self.result_marshal)

        return jsonify({'code': 20000, 'data': result, 'total': total})

    def build_search_body(self, args: dict) -> dict:
        """构建es查询条件"""
        # 组成查询条件（must）
        must_match_body = []
        # 应用
        if args.get('app'):
            must_match_body.append({'match_phrase': {'app': args.get('app')}})
        # 动作
        if args.get('action'):
            must_match_body.append({'match_phrase': {'action': args.get('action')}})
        # 模块
        if args.get('module'):
            must_match_body.append({'match_phrase': {'module': args.get('module')}})
        # 内容关键字
        if args.get('content'):
            must_match_body.append({'match_phrase': {'content': args.get('content')}})
        # 时间范围
        if args.get('start_datetime') or args.get('end_datetime'):
            op_timestamp = {'range': {
                'operatorInfo.timeStamp': {
                    'gte': args.get('start_datetime'),
                    'lte': args.get('end_datetime')
                }
            }}
            must_match_body.append(op_timestamp)
        # 查询操作人编号
        if args.get('operatorinfo_name'):
            operationinfo_name = {'term': {
                'operatorInfo.name.keyword': {
                    'value': args.get('operatorinfo_name')
                }
            }}
            must_match_body.append(operationinfo_name)
        # 查询操作人姓名
        if args.get('operatorinfo_displayname'):
            operationinfo_displayname = {'term': {
                'operatorInfo.displayName.keyword': {
                    'value': args.get('operatorinfo_displayname')
                }
            }}
            must_match_body.append(operationinfo_displayname)
        # 组成查询条件
        body = {
            'query': {'bool': {'must': must_match_body}},
            'sort' : {'operatorInfo.timeStamp': {'order': 'desc'}},
        }
        print(body)
        return body

    @staticmethod
    def parse_content(item: dict):
        """
        根据应用解析content字段
        @type item: dict
        """
        if item['app'] == 'Default':
            content = json.loads(item['content'])
            if item['action'] == '预览下载':
                item['content'] = content.get('name')
            elif item['action'] == '下载':
                item['content'] = content.get('fileName')
        elif item['app'] == 'LumiBox':
            content: dict = eval(item['content'])
            action = item['action']

            if action in ('数据/上传文件', '数据/同步上传'):
                item['content'] = content.get('to_path') + '/' + content.get('to_name')
            elif action in ('数据/下载文件', '数据/同步下载', '外链/下载', '外链/创建', '数据/预览文件', '数据/删除文件'):
                item['content'] = content.get('from_path', '') + '/' + content.get('from_name', '')
            elif action == '用户/登录':
                item['content'] = content.get('user_name', '')


class LumiAppLogsDownload(LumiAppLogs):
    """LumiApp的日志下载"""
    search_size = 10000

    def get(self):
        # 0 验证请求参数
        args = self.validation_params()
        # 0.1 构建es查询body
        body = self.build_search_body(args)
        # 1 查询数据库
        result = lumi_es.search(
            index=self.index,
            scroll='5m',
            size=self.search_size,
            body=body,
        )
        df_data = []  # 保存查询结果
        result_data = [i['_source'] for i in result['hits']['hits']]
        df_data.extend(result_data)
        # 1.1 继续通过游标查询（scroll_id)查询
        scroll_id = result['_scroll_id']
        while True:
            result = lumi_es.scroll(scroll_id=scroll_id, scroll='5m')
            result_data = [i['_source'] for i in result['hits']['hits']]

            if len(result_data) != 0:
                df_data.extend(result_data)

            if len(result_data) < self.search_size:
                break
        # 2 处理content字段
        with ThreadPoolExecutor(max_workers=self.page_count) as executor_pool:
            executor_pool.map(LumiAppLogs.parse_content, df_data)
        # 2.1 处理operatorInfo字段
        df = pd.DataFrame(data=df_data)
        df_operatorinfo = df['operatorInfo'].apply(pd.Series)
        df = pd.concat([df, df_operatorinfo], axis=1).drop(['operatorInfo', 'extraInformation'], axis=1)
        df['timeStamp'] = df['timeStamp'].astype('datetime64[ns]')
        df['timeStamp'] = df['timeStamp'] + timedelta(hours=8)
        # 3 构建excel数据
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer)
        writer.save()
        output.seek(0)

        return send_file(
            output,
            attachment_filename='lumi-op-logs.xlsx',
            as_attachment=True,
            mimetype='text/csv/xlsx'
        )


class LumiAppLogsSearchCount(Resource):
    parser = reqparse.RequestParser()

    def __init__(self):
        self.index = ''
        self.count = 0

    def post(self):
        self.parser.add_argument('dsl', type=str, default='', location='json', help='验证错误')
        params = self.parser.parse_args()
        # 解析dsl参数
        dsl = json.loads(params.get('dsl'))
        self.index = dsl.get('index')
        dsl_list = dsl.get('dsl_body')

        with ThreadPoolExecutor(max_workers=len(dsl_list)) as executor_pool:
            executor_pool.map(self.search_count, dsl_list)

        return jsonify({'code': 20000, 'count': self.count})

    def search_count(self, body: dict):
        result = lumi_es.count(
            index=self.index,
            body=body
        )
        self.count += result['count']


class LumiAppLogsSearchProCount(Resource):
    parser = reqparse.RequestParser()

    def __init__(self):
        self.index = ''
        self.result = {}

    def post(self):
        self.parser.add_argument('index', type=str, default='', location='json', help='验证错误')
        self.parser.add_argument('query_body', type=list, default='', location='json', help='验证错误')
        params = self.parser.parse_args()

        # 解析dsl参数
        self.index = params.get('index')
        dsl_list = params.get('dsl_body')

        with ThreadPoolExecutor(max_workers=len(dsl_list)) as executor_pool:
            executor_pool.map(self.search_count, dsl_list)

        return jsonify({'code': 20000, 'result': self.result})

    def search_count(self, body: dict):
        result = lumi_es.count(
            index=self.index,
            body=body['query']
        )
        self.result[body['id']] = result['count']


class LumiAppUserOpLogCount(Resource):
    parser = reqparse.RequestParser()

    search_size = 5000

    def post(self):
        self.parser.add_argument('index', type=str, default='', location='json', help='验证错误')
        self.parser.add_argument('query_body', type=str, default='', location='json', help='验证错误')
        data = self.parser.parse_args()
        query_body = json.loads(data.get('query_body'))

        result = lumi_es.search(
            index=data.get('index'),
            scroll='5m',
            size=self.search_size,
            body=query_body,
        )
        df_data = []  # 保存查询结果
        result_data = [i['_source'] for i in result['hits']['hits']]
        df_data.extend(result_data)
        # 1.1 继续通过游标查询（scroll_id)查询
        scroll_id = result['_scroll_id']
        while True:
            result = lumi_es.scroll(scroll_id=scroll_id, scroll='5m')
            result_data = [i['_source'] for i in result['hits']['hits']]

            if len(result_data) != 0:
                df_data.extend(result_data)

            if len(result_data) < self.search_size:
                break

        if len(df_data) == 0:
            return jsonify({'code': 20000, 'data': {}})

        df = pd.DataFrame(data=df_data)
        df_operatorinfo = df['operatorInfo'].apply(pd.Series)
        df = pd.concat([df, df_operatorinfo], axis=1)
        name_group = df.groupby('name').count()
        result = name_group['app'].to_dict()

        return jsonify({'code': 20000, 'data': result})


class AlbbChangeLog(Resource):

    def post(self):
        # 创建albb变更记录表，插入response的json数据

        pass


class Zscq(Resource):
    limit = 15
    parser = reqparse.RequestParser()
    result_marshal = {
        'apply_user_name'  : fields.String,
        'conutry_name'     : fields.String,
        'product_type'     : fields.String,
        'record_begin_date': fields.String,
        'record_end_date'  : fields.String,
        'record_icon'      : fields.String,
        'record_name'      : fields.String,
        'record_num'       : fields.String,
        'record_state'     : fields.String,
        'register_num'     : fields.String,
        'register_type'    : fields.String,
        'customer_code'    : fields.String,
        'customer_name'    : fields.String
    }

    def get(self):
        self.parser.add_argument('code', type=str, default='', location='values', help='验证错误')
        self.parser.add_argument('user_code', type=str, default='', location='values', help='验证错误')
        args = self.parser.parse_args()

        customer_code = args.get('code')
        user_code = args.get('user_code')

        mssql_conf = {
            'server'  : current_app.config.get('MSSQL_SERVER'),
            'user'    : current_app.config.get('MSSQL_USER'),
            'password': current_app.config.get('MSSQL_PASSWORD'),
            'database': current_app.config.get('MSSQL_DATABASE'),
        }
        with pymssql.connect(**mssql_conf) as conn:

            with conn.cursor(as_dict=True) as cursor:

                token = request.headers.get('X-Token')
                permission = self.get_permission(token)
                # 可以查看所有品牌权限
                if 'Spider.ZSCQ.Admin' in permission and not customer_code:
                    _sql = '''select * from dbo.zscq_brand 
                    left join dbo.zscq on zscq.record_name = zscq_brand.brand_name 
                    where record_name is not null'''
                    cursor.execute(_sql)
                    result: list = cursor.fetchall()

                    return jsonify({'code': 20000, 'data': marshal(result, self.result_marshal)})

                # 查询单个客户编码下品牌
                if customer_code:
                    # 判断用户是否有客户权限
                    customer_permission_api = current_app.config.get('CUSTOMER_PERMISSION')
                    body = {
                        'qcbm'    : customer_code,
                        'userCode': user_code
                    }
                    response = requests.post(customer_permission_api, json=body)
                    if not response.json().get('result'):
                        return jsonify({'code': 50000, 'message': '您还没有当前客户权限'})

                    _sql1 = """select * from 
                    dbo.zscq_brand left join dbo.zscq on zscq.record_name = zscq_brand.brand_name 
                    where customer_code = %s and record_name is not null"""
                    cursor.execute(_sql1, str(customer_code))
                    result: list = cursor.fetchall()
                    return jsonify({'code': 20000, 'data': marshal(result, self.result_marshal)})

                # 获取用户权限下能见的品牌
                elif user_code:
                    get_customer_api = current_app.config.get('CUSTOMER_LIST')
                    response = requests.post(get_customer_api, json={'userCode': user_code})
                    response_json = response.json().get("result", [])
                    custorm_code_list = set([i.get('code') for i in response_json])

                    if custorm_code_list:
                        sql_all = '''select * from dbo.zscq_brand 
                        left join dbo.zscq on zscq.record_name = zscq_brand.brand_name 
                        where record_name is not null'''
                        cursor.execute(sql_all)

                        result = []
                        for itme in cursor.fetchall():
                            if itme.get('customer_code') in custorm_code_list:
                                result.append(itme)

                        # _sql1 = """select * from dbo.zscq_brand where user_code = '{}'""".format(user_code)
                        # 客户编码太多导致sql查询错误，切片0-100
                        # _sql2 = """select * from dbo.zscq_brand
                        # left join dbo.zscq on zscq.record_name = zscq_brand.brand_name
                        # where customer_code in {} and record_name is not null""".format(tuple(custorm_code_list))
                        # cursor.execute(_sql2)
                        # result: list = cursor.fetchall()
                        return jsonify({'code': 20000, 'data': marshal(result, self.result_marshal)})

                    else:
                        return jsonify({'code': 20000, 'data': []})

    @cache.cached(timeout=60 * 5)
    def get_permission(self, token):
        # 1 请求渠成认证接口，获取用户信息
        response = requests.get(
            url=current_app.config.get('USERINFO_URL'),
            headers={'Authorization': token})
        result_json = response.json()
        user_info: dict = result_json.get('result', {})
        # 2 请求渠成权限中心，获取用户权限列表
        response = requests.post(
            url=current_app.config.get('PERMISSION_URL'),
            headers={'Authorization': token},
            json={
                "applicationName": "Spider",
                "moduleName"     : "string",
                "specUserName"   : user_info['userName']
            })
        result_json = response.json()
        items = result_json.get('result').get('items')
        permission: list = [i['name'] for i in items]
        return permission


# 不可用
class GJJAutoForm(Resource):
    URL = 'http://gjjwt.nbjs.gov.cn:7001/gjj-wsyyt/ajax/ejx4web.action'
    cookies = None
    company_info = None

    def post(self):
        data = json.loads(request.data)

        company = data.get('company')
        # todo acccount 如何通过js获取
        account = data.get('account')
        cookies_str = data.get('cookies')
        # 格式化cookies
        self.cookies = {i.split('=')[0]: i.split('=')[1] for i in cookies_str.split('; ')}
        # 获取单位信息
        self.company_info = self.get_company_info(account)
        # 查询指令
        server = current_app.config.get('MSSQL_SERVER')
        user = current_app.config.get('MSSQL_USER')
        password = current_app.config.get('MSSQL_PASSWORD')
        database = current_app.config.get('MSSQL_DATABASE')
        with DBConnection(server, user, password, database) as cursor:
            sql = """select * from dbo.hr_auto
            where type = '公积金' and status != 1 and salary != 0 and adjust_date <= %s and company = %s
            """
            cursor.execute(sql, (datetime.now().strftime('%Y-%m-%d'), company))
            result = cursor.fetchall()

            for user in result:
                self.declare(account, user)

            sql = """select * from dbo.hr_auto 
            where type = '公积金' and status != 1 and salary = 0 and adjust_date <= %s and company = %s
            """
            cursor.execute(sql, (datetime.now().strftime('%Y-%m-%d'), company))
            result = cursor.fetchall()
            for user in result:
                self.declare_stop(account, user)

        return 'ok'

    def get_user_info(self, account, cookies, user_number):
        """获取公积金账号"""
        form = {"accnum": "", "chgtype": "5", "certinum": user_number}
        body = {
            '_sid': 'personAddSealAndCallInService_addPersonAlter',
            'uid' : f'{account}-3',
            'json': form
        }
        response = requests.post(
            url=self.URL,
            cookies=cookies,
            json=body
        )
        return response.json()

    def get_company_info(self, account: str):
        """获取单位信息"""
        body = {
            '_sid': 'unitYearBaseAdjustService_getUnitInfo',
            'uid' : f'{account}-3',
            'json': {"unitaccnum": account}
        }
        response = requests.post(self.URL, data=body, cookies=self.cookies)
        return response.json()

    def get_monpaysum(self, account, salary, maxbasenum_eb, minbasenum_eb, unitprop):
        """获取 月存缴额"""
        form = {
            "monincome"  : salary,
            "zdjcjs"     : minbasenum_eb,
            "zgjcjs"     : maxbasenum_eb,
            "subunitprop": unitprop,
            "subindiprop": unitprop
        }
        body = {
            '_sid': 'personAddSealAndCallInService_calmonpaysum',
            'uid' : f'{account}-3',
            'json': form
        }
        response = requests.post(self.URL, data=body, cookies=self.cookies)
        return response.json().get('monpaysum')

    def declare(self, account, user):
        """申报"""
        # 获取个人账号
        user_info = self.get_user_info(account, self.cookies, user.get('user_number'))
        accnum = user_info.get('obj', {}).get('accnum')
        user['accnum'] = accnum
        # 获取月缴存额
        monpaysum = self.get_monpaysum(
            account,
            user.get('salary'),
            self.company_info.get('maxbasenum_eb'),
            self.company_info.get('minbasenum_eb'),
            self.company_info.get('unitprop'),
        )
        user['monpaysum'] = monpaysum

        if not accnum:
            return self.declare_open(account, user)

        return self.declare_diaoru(account, user)

    def declare_diaoru(self, account: str, user: dict):
        """调入"""
        form = {
            "chgtype"   : "5",
            "accnum"    : user.get('accnum'),
            "accname"   : user.get('name'),
            "certitype" : "1",
            "certinum"  : user.get('user_number'),
            "unitprop"  : self.company_info.get('unitprop'),
            "indiprop"  : self.company_info.get('unitprop'),
            "monincome" : "%2f" % user.get('salary'),
            "basenum"   : "%2f" % user.get('salary'),
            "monpaysum" : user.get('monpaysum'),
            "handset"   : "",
            "cenregtype": "1",
            "marstatus" : "1",
            "sealren"   : "",
            "unitaccnum": account
        }
        body = {
            '_sid': 'personAddSealAndCallInService_addPersonAlter',
            'uid' : f'{account}-3',
            'json': form
        }
        response = requests.post(
            url=self.URL,
            cookies=self.cookies,
            json=body
        )

        return response.json()

    def declare_open(self, account: str, user: dict):
        """开户"""
        form = {
            "chgtype"   : "1",
            "accnum"    : "",
            "accname"   : user.get('name'),
            "certitype" : "1",
            "certinum"  : user.get('user_number'),
            "unitprop"  : self.company_info.get('unitprop'),
            "indiprop"  : self.company_info.get('unitprop'),
            "monincome" : "%2f" % user.get('salary'),
            "basenum"   : "%2f" % user.get('salary'),
            "monpaysum" : user.get('monpaysum'),
            "handset"   : user.get('phone'),
            "cenregtype": "2",
            "marstatus" : "1",
            "sealren"   : "",
            "unitaccnum": account
        }
        body = {
            '_sid': 'personAddSealAndCallInService_addPersonAlter',
            'uid' : f'{account}-3',
            'json': form
        }
        response = requests.post(
            url=self.URL,
            cookies=self.cookies,
            json=body
        )
        return response.json()

    def declare_stop(self, account, user):
        """封存"""

        # 获取个人账号
        user_info = self.get_user_info(account, self.cookies, user.get('user_number'))
        user_info = user_info.get('obj', {})

        reason_map = [
            '解除劳动关系',
            '停职留薪',
            '退休',
            '违规违纪',
            '其他',
            '死亡',
        ]
        sealren = str(reason_map.index(user.get('bread_reason')) + 1)
        form = {
            "chgtype"   : "3",
            "accnum"    : user_info.get('accnum'),
            "accname"   : user.get('name'),
            "certitype" : "1",
            "certinum"  : user.get('user_number'),
            "unitprop"  : self.company_info.get('unitprop'),
            "indiprop"  : self.company_info.get('unitprop'),
            "monincome" : user_info.get('monincome'),
            "basenum"   : user_info.get('basenum'),
            "monpaysum" : user_info.get('monpaysum'),
            "handset"   : "",
            "cenregtype": "1",
            "marstatus" : "1",
            "sealren"   : sealren,
            "unitaccnum": account
        }
        body = {
            '_sid': 'personAddSealAndCallInService_addPersonAlter',
            'uid' : f'{account}-3',
            'json': form
        }
        response = requests.post(
            url=self.URL,
            cookies=self.cookies,
            json=body
        )
        return response.json()


class ReceivePhoneCode(Resource):
    '''接收手机验证码，手机收到验证码后会调用接口'''

    def post(self):
        print(request.form.to_dict())
        content = request.form.to_dict().get('content', '')  # 短信抓发起（不能转发短信平台发过来的）
        # content = request.form.to_dict().get('text', '')  # 恶搞大王通
        content = str(content)
        mssql_conf = {
            'server'  : current_app.config.get('MSSQL_SERVER'),
            'user'    : current_app.config.get('MSSQL_USER'),
            'password': current_app.config.get('MSSQL_PASSWORD'),
            'database': current_app.config.get('MSSQL_DATABASE'),
        }
        with pymssql.connect(**mssql_conf) as conn:

            with conn.cursor(as_dict=True) as cursor:
                sql = """insert into dbo.verify_code (code, content, source, create_datetime) values (%s, %s, %s, %s)"""

                if '智联招聘' in content and '验证码' in content:
                    result = re.findall(r'验证码：(\d+)', content)
                    code = result[0] if result else ''

                    cursor.execute(sql, (code, content, '智联招聘', datetime.now()))

                if '猎聘' in content and '验证码' in content:
                    result = re.findall(r'验证码：(\d+)', content)
                    code = result[0] if result else ''

                    cursor.execute(sql, (code, content, '猎聘', datetime.now()))

                if '浙江政务服务' in content and '验证码' in content:
                    result = re.findall(r'验证码为：(\d+)', content)
                    code = result[0] if result else ''
                    print(code)
                    cursor.execute(sql, (code, content, '浙江政务服务', datetime.now()))

            conn.commit()

        return 'ok'


class UUDI(Resource):
    '''UUID: 开发目的为RPA提供'''

    def get(self):
        return {'uuid': str(uuid.uuid4())}
