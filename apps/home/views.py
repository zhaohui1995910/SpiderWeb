from flask import jsonify, request
from bson import Code

from models import local_mongo
from apps.home import home


@home.route('/abc')
def abc():
    print('abc')
    return 'ok'


@home.route('/mongo/tree')
def mongo_tree():
    '''获取mongodb树结构'''
    result = dict()
    db_name_list = set(local_mongo.cx.list_database_names())
    result['dbList'] = list(db_name_list.difference({'admin', 'config', 'local'}))  # 差集
    result['db_coll_List'] = dict()

    for db_name in db_name_list:
        if db_name in ['admin', 'config', 'local']:
            continue
        item = dict()
        db = getattr(local_mongo.cx, db_name)
        c_name_list = list(db.list_collection_names(session=None))
        c_name_list.sort()
        item[db_name] = c_name_list
        result['db_coll_List'].update(item)

    return jsonify({'code': 20000, 'data': result})


@home.route('/mongo/coll/fields')
def mongo_coll_fields():
    '''获取集合下的字段列表'''
    db_name = request.args.get('db')
    coll_name = request.args.get('collection')

    db = getattr(local_mongo.cx, db_name)

    map_ = Code("function() { for (var key in this) { emit(key, null); } }")
    reduce = Code("function(key, stuff) { return null; }")
    field_list = db[coll_name].map_(map_, reduce, "myresults").distinct('_id')

    result = []
    for field in field_list:
        item = dict()
        item['key'] = field
        item['lable'] = field
        result.append(item)

    return jsonify({'code': 20000, 'data': result})
