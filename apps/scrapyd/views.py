import time
import json
from datetime import datetime, timedelta
from typing import List
from uuid import uuid1

import pymongo
import requests
import pandas as pd
from lxml import etree
from flask import jsonify, request
from flask_restful import Resource, reqparse, marshal, fields
from scrapyd_api import ScrapydAPI
from bson.objectid import ObjectId
from flask import current_app as app

from models import local_mongo
from models.scrapyd import *
from apps.scrapyd import tasks
from apps.scrapyd import scrapyd as ltscrapyd
from extension.scheduler import scheduler


class ServerInfo(Resource):
    '''Servers 模块'''
    parser = reqparse.RequestParser()

    def get(self):
        '''获取scrapyd server负载信息'''
        db = local_mongo.cx['spider_web']
        server_list = list(db.spider_manage_server.find({}, {'_id': 0}))

        for item in server_list:
            item['label'] = item.get('host') + ':' + item.get('port')

        return jsonify({'code': 20000, 'data': server_list})

    def post(self):
        '''添加scrapyd server服务器'''
        self.parser.add_argument('host', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('port', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('auth', type=bool, default=False, location='json', help='验证错误')
        self.parser.add_argument('username', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('password', type=str, default="", location='json', help='验证错误')
        args = self.parser.parse_args()
        server_item = {
            'host'         : args.get('host'),
            'port'         : args.get('port'),
            'auth'         : args.get('auth'),
            'auth_username': args.get('username'),
            'auth_password': args.get('password')
        }
        db = local_mongo.cx['spider_web']
        db.spider_manage_server.insert_one(server_item)

        return jsonify({'code': 20000, 'data': 'ok'})

    def delete(self):
        '''删除服务器配置'''
        self.parser.add_argument('host', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('port', type=str, default="", location='json', help='验证错误')
        args = self.parser.parse_args()
        db = local_mongo.cx['spider_web']
        db.spider_manage_server.delete_one({'host': args.get('host'), 'port': args.get('port')})

        return jsonify({'code': 20000, 'data': 'ok'})


class Projects(Resource):
    '''获取去重后的项目列表'''

    def get(self):
        '''获取项目列表'''
        db = local_mongo.cx['spider_web']

        pipelines = [
            {'$group': {'_id': {'name': '$name', 'is_delete': '$is_delete'}}},
            {'$project': {'_id': 0, 'name': '$_id.name', 'status': '$_id.is_delete'}},
            {'$match': {'status': False}}
        ]
        result = db.spider_manage_project.aggregate(pipelines)
        result = list(map(lambda r: r['name'], result))

        return jsonify({'code': 20000, 'data': result})


class ProjectInfo(Resource):
    '''Projects 模块'''
    limit = 18
    parser = reqparse.RequestParser()
    result_marshal = {
        "create_time": fields.String,
        "hostName"   : fields.String,
        "is_delete"  : fields.String,
        "name"       : fields.String,
        "desc"       : fields.String,
        "port"       : fields.String,
        "server"     : fields.String,
        "version"    : fields.String,
    }

    def get(self):
        '''获取项目列表'''
        page: int = int(request.args.get('page', default=1))
        project: str = request.args.get('project', default=None)

        # 获取服务器列表
        servers = self.get_server()
        servers_host = [s['host'] for s in servers]

        # 获取项目列表
        filter_dict = {
            'is_delete': False,
            'server'   : {'$in': servers_host}
        }
        if project:
            filter_dict['name'] = project
        db = local_mongo.cx['spider_web']
        find_project = db.spider_manage_project.find(
            filter_dict, {'_id': 0},
            sort=[("version", pymongo.DESCENDING)]
        ).skip(self.limit * (page - 1)).limit(self.limit)

        project_count = db.spider_manage_project.find(
            filter_dict, {'_id': 0},
            sort=[("version", pymongo.DESCENDING)]
        ).count()

        result = [p for p in find_project]

        return jsonify({
            'code'      : 20000,
            'data'      : marshal(result, self.result_marshal),
            'servers'   : servers,
            'data_count': project_count
        })

    def post(self):
        '''更新项目，简介，删除..'''
        self.parser.add_argument('project', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('desc', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('domains', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('server', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('hostname', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('version', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('is_delete', type=str, default="", location='json', help='验证错误')
        args = self.parser.parse_args()
        db = local_mongo.cx['spider_web']
        db.spider_manage_project.update_one(
            {
                'name'   : args.get('project'),
                'version': args.get('version')
            },
            {
                '$set': {
                    'desc'     : args.get('desc'),
                    'domain'   : args.get('domains'),
                    'is_delete': bool(args.get('is_delete'))
                }
            }

        )

        return jsonify({'code': 20000, 'data': 'ok'})

    def get_server(self) -> list:
        '''获取服务器列表'''
        db = local_mongo.cx['spider_web']
        find_server = db.spider_manage_server.find(
            {'is_delete': False}, {'_id': 0}
        )
        servers = [i for i in find_server]
        servers_host = [s['host'] for s in servers]

        for s in servers:
            s['label'] = s.get('host') + ':' + s.get('port')

        return servers


class ProjectSpider(Resource):
    '''Projects “Spider” 按钮'''
    parser = reqparse.RequestParser()

    def get(self):
        '''获取爬虫列表 及爬虫简介'''
        db = local_mongo.cx['spider_web']
        server_list = list(db.spider_manage_server.find({}, {'host': 1, 'port': 1}))
        server_host_list = [server.get('host') for server in server_list]
        # server_port_list = [server.get('port') for server in server_list]

        self.parser.add_argument('host', choices=server_host_list, location='values', help='验证错误')
        self.parser.add_argument('port', type=str, location='values', help='验证错误')
        self.parser.add_argument('project', type=str, default="", location='values', help='验证错误')
        self.parser.add_argument('version', type=str, default="", location='values', help='验证错误')
        args = self.parser.parse_args()
        # 获取scrapyd爬虫列表

        spider_list = list(
            db.spider_manage_spider.find(
                {
                    'project': args.get('project'),
                    'version': args.get('version'),
                    'server' : args.get('host'),
                    'port'   : args.get('port')
                },
                {
                    '_id': 0
                }
            )
        )

        return jsonify({'code': 20000, 'data': spider_list})

    def post(self):
        '''更新或激活项目爬虫列表（项目爬虫列表添加到数据库）'''
        db = local_mongo.cx['spider_web']
        server_list = list(db.spider_manage_server.find({}, {'host': 1, 'port': 1}))
        # server_host_list = [server.get('host') for server in server_list]
        # server_port_list = [server.get('port') for server in server_list]

        self.parser.add_argument('host', type=str, default="", location='json', help='host 验证错误')
        self.parser.add_argument('port', type=str, default="", location='json', help='port 验证错误')
        self.parser.add_argument('project', type=str, default="", location='json', help='project 验证错误')
        self.parser.add_argument('version', type=str, default="", location='json', help='version 验证错误')
        args = self.parser.parse_args()

        scrapyd_item = db.spider_manage_server.find_one(
            {
                'host': args.get('host'),
                'port': args.get('port')
            }
        )

        if not scrapyd_item:
            return jsonify({'code': 50000, 'data': '没有找到scrapyd server'})

        # 获取爬虫列表
        spider_list = self.get_scrapyd_spiders(scrapyd_item, args.get('project'), args.get('version'))

        for spider in spider_list:
            # 获取爬虫简介 默认上一个版本的简介
            desc = self.get_spider_desc(
                project=args.get('project'),
                spider=spider,
                version=args.get('version')
            )
            # 存在则更新，不存在则新增
            db.spider_manage_spider.update_one(
                {
                    'name'   : spider,
                    'project': args.get('project'),
                    'version': args.get('version')
                },
                {
                    '$set': {
                        'name'   : spider,
                        'desc'   : desc,
                        'project': args.get('project'),
                        'server' : args.get('host'),
                        'port'   : args.get('port'),
                        'version': args.get('version')
                    }
                },
                upsert=True
            )

        return jsonify({'code': 20000, 'data': 'ok'})

    def get_scrapyd_spiders(self, server, project, version):
        '''获取scrapyd爬虫列表'''
        host = server.get('host')
        port = server.get('port')

        auth = server.get('auth')
        auth_username = server.get('auth_username')
        auth_password = server.get('auth_password')

        # 构建url
        url = f'http://{host}:{port}/listspiders.json?project={project}&_version={version}'
        # 获取认证信息
        auth = (auth_username, auth_password) if auth else None
        # 请求scrapyd服务获取爬虫列表
        spider_list = [spider for spider in requests.get(url, auth=auth).json().get('spiders', [])]

        return spider_list

    def get_spider_desc(self, project, spider, version):
        '''获取爬虫简介，小于等于当前版本的简介（优先等于）'''
        db = local_mongo.cx['spider_web']
        desc = ''
        spider_list = db.spider_manage_spider.find(
            {
                'project': project,
                'name'   : spider
            },
            sort=[('version', pymongo.DESCENDING)]
        )
        for item in spider_list:
            if item.get('desc') and int(item.get('version')) <= int(version):
                desc = item.get('desc')
                break
        return desc


class SpiderInfo(Resource):
    '''Spiders 模块'''
    limit = 15
    parser = reqparse.RequestParser()

    def get(self):
        '''获取爬虫列表，条件筛选'''
        db = local_mongo.cx['spider_web']
        project_item_list = db.spider_manage_project.find({'is_delete': True})
        project_version_list = set([item.get('version') for item in project_item_list])

        spider_list = list(
            db.spider_manage_spider.find(
                {
                    'version': {'$nin': list(project_version_list)}
                },
                {
                    '_id': 0
                },
                sort=[("version", pymongo.DESCENDING)]
            )
        )

        project_option = list(set([i.get('project') for i in spider_list]))
        spider_option = list(set([i.get('name') for i in spider_list])).sort()

        return jsonify({
            'code'         : 20000,
            'data'         : spider_list,
            'projectOption': project_option,
            'spiderOption' : spider_option
        })

    def post(self):
        '''更新爬虫简介, 在project模块的spider按钮中被调用'''
        self.parser.add_argument('project', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('version', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('spider', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('desc', type=str, default="", location='json', help='验证错误')
        args = self.parser.parse_args()
        db = local_mongo.cx['spider_web']
        db.spider_manage_spider.update_one(
            {
                'project': args.get('project'),
                'version': args.get('version'),
                'name'   : args.get('spider')
            },
            {
                '$set': {'desc': args.get('desc')}
            }
        )

        return jsonify({'code': 20000, 'data': 'ok'})


class TaskInfo(Resource):
    '''Timer Tasks 模块'''
    parser = reqparse.RequestParser()

    def get(self):
        '''获取tasks列表'''
        db = local_mongo.cx['spider_web']
        task_list = list(db.spider_manage_task.find({}))

        for task in task_list:
            task['id'] = str(task.pop('_id', ''))

        return jsonify({'code': 20000, 'data': task_list})

    def post(self):
        '''创建'''
        self.parser.add_argument('server', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('port', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('project', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('version', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('spider', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('name', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('desc', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('settings', type=dict, default="", location='json', help='验证错误')
        self.parser.add_argument('timer', type=dict, default="", location='json', help='验证错误')
        args = self.parser.parse_args()
        db = local_mongo.cx['spider_web']
        task = {
            'status'   : True,
            'trigger'  : 'cron',
            'run_count': 0,
            'server'   : args.get('server'),
            'port'     : args.get('port'),
            'project'  : args.get('project'),
            'version'  : args.get('version'),
            'spider'   : args.get('spider'),
            'name'     : args.get('name'),
            'desc'     : args.get('desc'),
            'settings' : self.handler_settings(args.get('settings')),
            'timer'    : args.get('timer'),
        }
        result = db.spider_manage_task.insert_one(task)
        try:
            # 创建定时任务
            add_result = scheduler.add_job(
                id=task.get('name'),
                func=tasks.start_job_task,
                trigger=task.get('trigger'),
                **args.get('timer'),
                kwargs={'task_id': str(result.inserted_id)},  # _id属性
            )
        except Exception as e:
            app.logger.error('TaskInfo 创建定时任务异常：%s' % e)
            db.spider_manage_task.delete_one({'_id': ObjectId(result.inserted_id)})
            return jsonify({'code': 20000, 'data': 'error'})
        else:
            # 更新任务下次运行时间
            job = scheduler.get_job(id=task.get('name'))
            # task 下次运行时间
            next_run_time = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')

            db.spider_manage_task.update_one(
                {'_id': result.inserted_id},
                {'$set': {'next_run_time': next_run_time}}
            )

        return jsonify({'code': 20000, 'data': 'ok'})

    def put(self):
        '''更新任务'''
        self.parser.add_argument('taskId', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('version', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('name', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('desc', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('settings', type=dict, default="", location='json', help='验证错误')
        args = self.parser.parse_args()
        db = local_mongo.cx['spider_web']
        db.spider_manage_task.update_one(
            {
                '_id': ObjectId(args.get('taskId'))
            },
            {
                '$set': {
                    'version' : args.get('version'),
                    'name'    : args.get('name'),
                    'desc'    : args.get('desc'),
                    'settings': self.handler_settings(args.get('settings')),
                }
            }
        )

        return jsonify({'code': 20000, 'data': 'ok'})

    def handler_settings(self, settings):
        '''处理settings'''
        result = {}
        additional = settings.get('additional')
        # 删除没有设置的配置
        for s in settings:
            if settings[s] and s != 'additional':
                result[s] = settings.get(s)
        # 处理额外的参数
        if additional:
            kv_str = additional.split()  # additional 格式必须正确 否则报错
            result['additional'] = '&'.join(kv_str)

        return result


class TaskHistory(Resource):
    '''Timer Tasks 模块中的History按钮'''

    def get(self):
        '''获取task的job历史记录'''
        pass


class TaskDelete(Resource):
    '''Timer Tasks 模块中的Delete按钮'''
    parser = reqparse.RequestParser()

    def post(self):
        '''删除task'''
        db = local_mongo.cx['spider_web']
        self.parser.add_argument('taskId', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('taskName', type=str, default="", location='json', help='验证错误')
        args = self.parser.parse_args()

        # 删除定时任务
        scheduler.remove_job(args.get('taskName')) if scheduler.get_job(args.get('taskName')) else None
        # 删除数据库任务
        db.spider_manage_task.delete_one(
            {'_id': ObjectId(args.get('taskId'))}
        )

        return jsonify({'code': 20000, 'data': 'ok'})


class TaskStatus(Resource):
    '''Timer Tasks 模块中的Status按钮'''
    parser = reqparse.RequestParser()

    def post(self):
        '''切换task状态（task 暂停/恢复）'''
        self.parser.add_argument('taskId', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('status', type=bool, default="", location='json', help='验证错误')
        args = self.parser.parse_args()
        db = local_mongo.cx['spider_web']

        task = db.spider_manage_task.find_one({'_id': ObjectId(args.get('taskId'))})
        status = not bool(args.get('status'))  # 任务状态取反

        # 暂定和恢复定时任务
        if not task.get('status'):
            scheduler.resume_job(task.get('name'))
            job = scheduler.get_job(task.get('name'))
            next_run_time = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            scheduler.pause_job(task.get('name'))
            next_run_time = None

        # 更新task的状态和下次运行时间
        db.spider_manage_task.update_one(
            {
                '_id': ObjectId(args.get('taskId'))
            },
            {'$set': {
                'status'       : status,
                'next_run_time': next_run_time}
            }
        )

        return jsonify({'code': 20000, 'data': 'ok'})


class JobsInfo(Resource):
    '''Jobs 模块'''
    parser = reqparse.RequestParser()
    limit = 18
    result_marshal = {
        "datas"      : fields.String,
        "finish_time": fields.String,
        "id"         : fields.String(attribute=lambda x: x['_id']),
        "is_delete"  : fields.String,
        "items"      : fields.String(attribute=lambda x: x.get('items', '0')),
        "job"        : fields.String,
        "pages"      : fields.String(default='0'),
        "port"       : fields.String,
        "project"    : fields.String,
        "runtime"    : fields.String,
        "server"     : fields.String,
        "spider"     : fields.String,
        "start_time" : fields.String,
        "status"     : fields.String,
        "taskId"     : fields.String,
        "update_time": fields.String,
        "version"    : fields.String
    }

    def get(self):
        '''获取job列表'''
        self.parser.add_argument('page', type=int, default=1, location='values', help='验证错误')
        self.parser.add_argument('project', type=str, default='', location='values', help='验证错误')
        self.parser.add_argument('version', type=str, default='', location='values', help='验证错误')
        self.parser.add_argument('spider', type=str, default='', location='values', help='验证错误')
        self.parser.add_argument('start_time', type=str, default='', location='values', help='验证错误')
        self.parser.add_argument('end_time', type=str, default='', location='values', help='验证错误')
        self.parser.add_argument('taskId', type=str, default='', location='values', help='验证错误')
        args = self.parser.parse_args()

        filter = {'is_delete': False}

        if args.get('project'):
            filter['project'] = args.get('project')

        if args.get('version'):
            filter['version'] = args.get('version')

        if args.get('spider'):
            filter['spider'] = args.get('spider')

        if args.get('start_time'):
            filter['start_time'] = {'$gte': args.get('start_time')}

        if args.get('end_time'):
            filter['end_time'] = {'$lte': args.get('end_time')}

        if args.get('taskId'):
            filter['taskId'] = args.get('taskId')
        db = local_mongo.cx['spider_web']
        result = db.spider_manage_job.find(
            filter,
            sort=[('start_time', pymongo.DESCENDING)]
        ).skip(self.limit * (args.get('page') - 1)).limit(self.limit)

        data_count = db.spider_manage_job.find(
            filter,
            sort=[('start_time', pymongo.DESCENDING)]
        ).count()

        return jsonify({
            'code'      : 20000,
            'data'      : marshal(list(result), self.result_marshal),
            'data_count': data_count})

    def post(self):
        '''删除job'''
        self.parser.add_argument('jobId', type=str, default="", location='json', help='验证错误')
        self.parser.add_argument('is_delete', type=bool, default=False, location='json', help='验证错误')
        args = self.parser.parse_args()
        db = local_mongo.cx['spider_web']
        db.spider_job.update_one(
            {
                '_id': ObjectId(args.get('jobId'))
            },
            {
                '$set': {'is_delete': True}
            }
        )

        return jsonify({'code': 20000, 'data': 'ok'})


class JobInfo(Resource):
    '''Jobs 模块中的Fresh按钮'''
    parser = reqparse.RequestParser()

    def get(self):
        '''获取单条task（刷新单条 task状态）'''
        self.parser.add_argument('jobId', type=str, default="", location='values', help='验证错误')
        args = self.parser.parse_args()
        db = local_mongo.cx['spider_web']
        job_item = db.spider_manage_job.find_one({'_id': ObjectId(args.get('jobId'))})

        return jsonify(
            {
                'code': 20000,
                'data': dict(job_item)
            }
        )


class LogsList(Resource):
    '''Logs 模块'''
    parser = reqparse.RequestParser()

    def get(self):
        '''选择爬虫，获取logs列表'''
        self.parser.add_argument('host', type=str, default="", location='values', help='验证错误')
        self.parser.add_argument('port', type=str, default="", location='values', help='验证错误')
        self.parser.add_argument('project', type=str, default="", location='values', help='验证错误')
        self.parser.add_argument('spider', type=str, default="", location='values', help='验证错误')
        args = self.parser.parse_args()
        db = local_mongo.cx['spider_web']
        server_item = db.spider_manage_server.find_one(
            {
                'host': args.get('host'),
                'port': args.get('port')
            }
        )

        if not server_item:
            return jsonify({'code': 50000, 'data': '没有找到scrapyd server'})

        result = self.get_scrapyd_logs(server_item, args.get('project'), args.get('spider'))

        return jsonify({'code': 20000, 'data': result})

    def get_scrapyd_logs(self, server, project, spider):
        '''获取scrapyd的logs列表'''
        host, port = server.get('host'), server.get('port')

        url = f'http://{host}:{port}/logs/{project}/{spider}/'
        auth = (server.get('auth_username'), server.get('auth_password')) if server.get('auth') else None
        content = requests.get(url, auth=auth).content

        logs = []
        html = etree.HTML(content)
        tr_list = html.xpath('//tr')
        for tr in tr_list:
            item = dict()
            item['logName'] = ''.join(tr.xpath('./td[1]/a/text()'))
            item['logSize'] = ''.join(tr.xpath('./td[2]/text()'))
            item['logType'] = ''.join(tr.xpath('./td[3]/text()'))
            item['logEncode'] = ''.join(tr.xpath('./td[4]/text()'))
            logs.append(item) if item['logName'] else None

        return logs


class LogInfo(Resource):
    '''Logs 模块'''
    parser = reqparse.RequestParser()

    def get(self):
        '''获取日志内容'''
        self.parser.add_argument('host', type=str, default="", location='values', help='验证错误')
        self.parser.add_argument('port', type=str, default="", location='values', help='验证错误')
        self.parser.add_argument('project', type=str, default="", location='values', help='验证错误')
        self.parser.add_argument('spider', type=str, default="", location='values', help='验证错误')
        self.parser.add_argument('logName', type=str, default="", location='values', help='验证错误')
        args = self.parser.parse_args()
        db = local_mongo.cx['spider_web']
        server_item = db.spider_manage_server.find_one(
            {
                'host': args.get('host'),
                'port': args.get('port')
            }
        )

        if not server_item:
            return jsonify({'code': 50000, 'data': '没有找到scrapyd server'})

        # 获取日志
        try:
            result = self.get_scrapy_log(
                server=server_item,
                project=args.get('project'),
                spider=args.get('spider'),
                log_name=args.get('logName')
            )
        except Exception as e:
            app.logger.error('请求日志异常: %s' % e)
            result = '请求日志异常'
        # 日志分析，更新job表
        try:
            self.update_job(args.get('logName'), result)
        except Exception as e:
            app.logger.error('scrapyd 日志解析异常: %s, %s' % (args.get('logName'), e))

        return jsonify({'code': 20000, 'data': result})

    def get_scrapy_log(self, server, project, spider, log_name):
        '''获取scrapyd日志内容'''
        host, port = server.get('host'), server.get('port')
        auth = (server.get('auth_username'), server.get('auth_password')) if server.get('auth') else None
        url = f'http://{host}:{port}/logs/{project}/{spider}/{log_name}'

        content = requests.get(url, auth=auth).content.decode()
        return content

    def update_job(self, job_name, log_json):
        if '.json' in job_name:
            job_name = job_name.replace('.json', '')
            log_data = json.loads(log_json)
            pages = log_data.get('pages') if log_data.get('pages') else 0
            items = log_data.get('items') if log_data.get('items') else 0
            db = local_mongo.cx['spider_web']
            db.spider_manage_job.update_one(
                {
                    'job': job_name
                },
                {
                    'pages': pages,
                    'items': items
                }
            )


class Schedule(Resource):
    '''安排一次蜘蛛运行（也称为作业），并返回作业ID'''

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('spider', type=str, default="", location='json', help='验证错误')
        parser.add_argument('project', type=str, default="", location='json', help='验证错误')
        parser.add_argument('server', type=str, default="", location='json', help='验证错误')
        parser.add_argument('port', type=str, default="", location='json', help='验证错误')
        parser.add_argument('jobid', type=str, default="", location='json', help='验证错误')
        parser.add_argument('version', type=str, default="", location='json', help='验证错误')
        parser.add_argument('settings', type=dict, default="", location='json', help='验证错误')
        args = parser.parse_args()
        db = local_mongo.cx['spider_web']
        host, port = args.get('server'), args.get('port')
        server_item = db.spider_manage_server.find_one(
            {
                'host': host,
                'port': port
            },
        )

        target = f'http://{host}:{port}'
        auth = (server_item.get('auth_username'), server_item.get('auth_password')) if server_item.get('auth') else None
        scrapy_api = ScrapydAPI(target=target, auth=auth, timeout=10)
        # 处理settings参数
        settings, additional = self.handler_settings(args.get('settings'))
        # jobid 默认为当前时间戳
        jobid = args.get('jobid') if args.get('jobid') else str(int(time.time()))
        # 调度爬虫
        result = scrapy_api.schedule(
            project=args.get('project'),
            spider=args.get('spider'),
            settings=settings,
            jobid=jobid,
            version=args.get('version'),
            **additional
        )
        # 创建任务
        db.spider_manage_job.insert_one(
            {
                'server'    : args.get('server'),
                'port'      : args.get('port'),
                'project'   : args.get('project'),
                'version'   : args.get('version'),
                'spider'    : args.get('spider'),
                'job'       : jobid,
                'status'    : 'pending',
                'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'is_delete' : False
            }
        )

        return jsonify({'code': 20000, 'data': result})

    def handler_settings(self, settings):
        '''处理settings'''
        settings_result = {}
        additional_result = {}
        # 删除没有设置的配置
        for s in settings:
            if settings[s] and s != 'additional':
                settings_result[s] = settings[s]
        # 处理额外的参数
        additional = settings.get('additional')
        if additional:
            item_list = additional.split()
            for item in item_list:
                k, v = item.split('=')
                additional_result[k] = v

        return settings_result, additional_result


class Cancel(Resource):
    '''取消蜘蛛运行（又称作业）。如果作业待处理，它将被删除。如果作业正在运行，它将终止。'''

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('server', type=str, default="", location='json', help='验证错误')
        parser.add_argument('port', type=str, default="", location='json', help='验证错误')
        parser.add_argument('project', type=str, default="", location='json', help='验证错误')
        parser.add_argument('job', type=str, default="", location='json', help='验证错误')
        args = parser.parse_args()
        db = local_mongo.cx['spider_web']
        host, port = args.get('server'), args.get('port')
        server_item = db.spider_manage_server.find_one(
            {
                'host': host,
                'port': port
            }
        )
        # 构建scrapyd的url
        target = f'http://{host}:{port}'
        # 获取scrapyd的认证
        auth = (server_item.get('auth_username'), server_item.get('auth_password')) if server_item else None
        # scrapyd客户端
        scrapyd_api = ScrapydAPI(target=target, auth=auth)
        # 取消爬虫
        result = scrapyd_api.cancel(project=args.get('project'), job=args.get('job'))

        return jsonify({'code': 20000, 'data': result})


class Stats(Resource):
    '''Jobs 模块的stats按钮'''
    parser = reqparse.RequestParser()

    def get(self):
        self.parser.add_argument('host', type=str, default="", location='values', help='验证错误')
        self.parser.add_argument('port', type=str, default="", location='values', help='验证错误')
        self.parser.add_argument('project', type=str, default="", location='values', help='验证错误')
        self.parser.add_argument('spider', type=str, default="", location='values', help='验证错误')
        self.parser.add_argument('jobName', type=str, default="", location='values', help='验证错误')
        self.parser.add_argument('jobid', type=str, default="", location='values', help='验证错误')
        args = self.parser.parse_args()
        db = local_mongo.cx['spider_web']
        server_item = db.spider_manage_server.find_one(
            {
                'host': args.get('host'),
                'port': args.get('port')
            }
        )
        if not server_item:
            return jsonify({'code': 50000, 'data': '没有找到scrapyd server'})

        log_name = args.get('jobName') + '.json'
        try:
            args['logName'] = log_name
            args.pop('jobName')
            logJson = self.get_scrapy_log(
                server=server_item,
                project=args.get('project'),
                spider=args.get('spider'),
                log_name=log_name
            )
        except Exception as e:
            return jsonify(
                {
                    'code' : 20000,
                    'data' : {
                        'Analysis': {},
                        'crawler' : {}
                    },
                    'error': '请求日志异常 %s' % log_name
                }
            )

        Analysis = dict()
        Analysis['project'] = args.get('project')
        Analysis['spider'] = args.get('spider')
        Analysis['jobName'] = log_name
        Analysis['first_log_time'] = logJson.get('first_log_time')
        Analysis['latest_log_time'] = logJson.get('latest_log_time')
        Analysis['runtime'] = logJson.get('runtime')
        Analysis['crawled_pages'] = logJson.get('pages')
        Analysis['scraped_items'] = logJson.get('items')
        Analysis['shutdown_reason'] = logJson.get('runtime')
        Analysis['finish_reason'] = logJson.get('runtime')
        Analysis['log_critical_count'] = logJson.get('log_categories', {}).get('critical_logs', {}).get('count')
        Analysis['log_error_count'] = logJson.get('log_categories', {}).get('error_logs', {}).get('count')
        Analysis['log_warning_count'] = logJson.get('log_categories', {}).get('warning_logs', {}).get('count')
        Analysis['log_redirect_count'] = logJson.get('log_categories', {}).get('redirect_logs', {}).get('count')
        Analysis['log_retry_count'] = logJson.get('log_categories', {}).get('retry_logs', {}).get('count')
        Analysis['log_ignore_count'] = logJson.get('log_categories', {}).get('ignore_logs', {}).get('count')
        Analysis['latest_crawl'] = logJson.get('latest_matches', {}).get('latest_crawl')
        Analysis['latest_scrape'] = logJson.get('latest_matches', {}).get('latest_scrape')
        Analysis['latest_item'] = logJson.get('latest_matches', {}).get('latest_item')

        crawler = dict()
        crawler['source'] = logJson.get('crawler_stats', {}).get('source')
        crawler['last_update_time'] = logJson.get('crawler_stats', {}).get('last_update_time')
        crawler['downloader_response_bytes'] = logJson.get('crawler_stats', {}).get('downloader/response_byte')
        crawler['downloader_response_count'] = logJson.get('crawler_stats', {}).get('downloader/response_count')
        crawler['downloader_response_status_count_200'] = logJson.get('crawler_stats', {}).get(
            'downloader/response_status_count/200')
        crawler['elapsed_time_seconds'] = logJson.get('crawler_stats', {}).get('elapsed_time_second')
        crawler['finish_reason'] = logJson.get('crawler_stats', {}).get('finish_reason')
        crawler['finish_time'] = logJson.get('crawler_stats', {}).get('finish_time')
        crawler['item_scraped_count'] = logJson.get('crawler_stats', {}).get('item_scraped_count')
        crawler['log_count_INFO'] = logJson.get('crawler_stats', {}).get('log_count/INFO')
        crawler['memusage_max'] = logJson.get('crawler_stats', {}).get('memusage/max')
        crawler['memusage_startup'] = logJson.get('crawler_stats', {}).get('memusage/startup')
        crawler['request_depth_max'] = logJson.get('crawler_stats', {}).get('downloader/response_byte')
        crawler['response_received_count'] = logJson.get('crawler_stats', {}).get('response_received_count')
        crawler['scheduler_dequeued'] = logJson.get('crawler_stats', {}).get('scheduler/enqueued')
        crawler['scheduler_dequeued_memory'] = logJson.get('crawler_stats', {}).get('scheduler/enqueued/memory')
        crawler['start_time'] = logJson.get('crawler_stats', {}).get('start_time')

        try:
            datas = self.handle_datas(logJson.get('datas'))
        except:
            datas = []

        return jsonify({'code': 20000, 'data': {'Analysis': Analysis, 'crawler': crawler, 'datas': datas}})

    def get_scrapy_log(self, server, project, spider, log_name):
        '''获取scrapyd日志内容'''
        host, port = server.get('host'), server.get('port')

        auth = (server.get('auth_username'), server.get('auth_password')) if server.get('auth') else None

        url = f'http://{host}:{port}/logs/{project}/{spider}/{log_name}'

        content = requests.get(url, auth=auth).json()
        return content

    def handle_datas(self, datas):
        '''处理scrapyd 爬虫日志中datas'''
        df = pd.DataFrame(data=datas)
        data = df.T.to_numpy()
        for i, x in enumerate(data[0]):
            if i != 0 or i != len(data[0]) - 1:
                data[0][i] = '.'

        return data.tolist()


class Dashboard(Resource):
    parser = reqparse.RequestParser()

    def get(self):
        self.parser.add_argument('jobid', type=str, default="", location='values', help='验证错误')
        args = self.parser.parse_args()
        db = local_mongo.cx['spider_web']
        job = db.spider_manage_job.find_one(
            {
                '_id': ObjectId(args.get('jobid'))
            }
        )

        if not job.get('datas'):
            return jsonify({'code': 50000, 'data': [[], [], [], [], []]})

        data = eval(job.datas)
        df = pd.DataFrame(data=data)
        array = df.T.to_numpy()

        result = dict()
        result['x'] = array[0]
        result['pagesSum'] = array[1]
        result['pagesMin'] = array[2]
        result['itemsSum'] = array[3]
        result['itemsMin'] = array[4]

        return jsonify({'code': 20000, 'data': array})


class DataViews(Resource):
    '''爬虫数据可视化'''

    def get(self):
        '''返回视图列表'''
        db = local_mongo.cx['spider_web']
        views_list = list(db.spider_manage_views.find())
        for views in views_list:
            views['id'] = str(views.pop('_id'))
            views['fields'] = ', '.join(views.get('fields', []))

        return jsonify({'code': 20000, 'data': views_list})

    def post(self):
        '''创建视图'''
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, location='json', help='验证错误')
        parser.add_argument('desc', type=str, default="", location='json', help='验证错误')
        parser.add_argument('db', type=str, location='json', help='验证错误')
        parser.add_argument('table', type=str, location='json', help='验证错误')
        parser.add_argument('fields', type=list, default=[], location='json', help='验证错误')
        parser.add_argument('project', type=str, location='json', help='验证错误')
        parser.add_argument('spider', type=str, location='json', help='验证错误')
        parser.add_argument('version', type=str, location='json', help='验证错误')

        args = dict(parser.parse_args())
        data_view = DataViewsModel(**args)
        data_view.insert('spider_manage_views')

        return jsonify({'code': 20000, 'data': '创建成功'})

    def put(self):
        '''修改视图配置'''
        parser = reqparse.RequestParser()
        parser.add_argument('viewId', type=str, location='json', help='验证错误')
        parser.add_argument('name', type=str, location='json', help='验证错误')
        parser.add_argument('desc', type=str, default="", location='json', help='验证错误')
        parser.add_argument('db', type=str, location='json', help='验证错误')
        parser.add_argument('table', type=str, location='json', help='验证错误')
        parser.add_argument('fields', type=list, default=[], location='json', help='验证错误')
        parser.add_argument('project', type=str, location='json', help='验证错误')
        parser.add_argument('spider', type=str, location='json', help='验证错误')
        parser.add_argument('version', type=str, location='json', help='验证错误')
        args = parser.parse_args()
        db = local_mongo.cx['spider_web']
        result = db.spider_manage_views.update_one(
            {
                '_id': args.get('viewId')
            },
            {
                '$set': args
            }
        )
        if result:
            return jsonify({'code': 20000, 'data': '更新成功'})

        return jsonify({'code': 20000, 'data': '更新失败'})

    def delete(self):
        '''删除视图'''
        db = local_mongo.cx['spider_web']
        parser = reqparse.RequestParser()
        parser.add_argument('viewId', type=str, location='json', help='验证错误')
        result = db.spider_manage_views.delete_one({'_id': parser.parse_args().get('viewId')})
        if result:
            return jsonify({'code': 20000, 'data': '删除成功'})

        return jsonify({'code': 20000, 'data': '删除失败'})


@ltscrapyd.route('/spider/tree')
def spider_tree():
    '''返回爬虫项目树结构'''
    db = local_mongo.cx['spider_web']
    result = dict()
    # 查询未删除的项目
    project_list = list(db.spider_manage_project.find({'is_delete': False}, {'_id': 0}))
    if not project_list:
        return jsonify({'code': 20000, 'data': '没有项目结构'})
    p_df = pd.DataFrame(project_list)
    pgroup = p_df.groupby(['name'])

    result['projectList'] = list(pgroup.groups)
    result['pvgx'] = dict()  # 项目和版本关系
    result['vsgx'] = dict()  # 版本和爬虫关系

    for g in result['projectList']:
        result['pvgx'][g] = pgroup.get_group(g)['version'].to_list()

    spider_list = list(db.spider_manage_spider.find({}, {'version': 1, 'name': 1}))

    if not spider_list:
        return jsonify({'code': 20000, 'data': '没有爬虫结构'})

    s_df = pd.DataFrame(spider_list)
    sgroup = s_df.groupby(['version'])

    for v in list(sgroup.groups):
        result['vsgx'][v] = sgroup.get_group(v)['name'].to_list()

    return jsonify({'code': 20000, 'data': result})


# @ltscrapyd.route('/data')
# def spider_date():
#     page = request.args.get('page')
#     view_id = request.args.get('viewid')
#     # 查询视图配置
#     view = db.spider_manage_views.find_one({'_id': view_id}, {'fields': 1, 'table': 1, 'db': 1})
#     # 连接要查询的集合
#     db = getattr(mongo.cx, view.get('db'))
#     collecton = getattr(db, view.get('table'))
#     # 设置-数据库返回的字段
#     fv = [1 for i in view['fields']]
#     fields = dict(zip(view.get('fields'), fv))
#     fields['_id'] = 0
#
#     filder_dict = dict()
#     sort_fields = list()
#     for field in view['fields']:
#         # 设置过滤条件
#         field_value = request.args.get(field, None)
#         field_value_list = field_value.split(';') if field_value else []
#
#         for fieldV in field_value_list:
#
#             if '$' not in fieldV:
#                 filder_dict[field] = fieldV
#                 continue
#             # 设置排序条件
#             if '$sort:asc' in fieldV:
#                 sort_fields.append((field, pymongo.ASCENDING))
#             if '$sort:desc' in fieldV:
#                 sort_fields.append((field, pymongo.DESCENDING))
#
#             if '$gt:' in fieldV:
#                 gtv = fieldV.replace('$gt:', '')
#                 filder_dict[field] = {'$gt': gtv}
#
#             if '$gte:' in fieldV:
#                 gtev = fieldV.replace('$gte:', '')
#                 filder_dict[field] = {'$gte': gtev}
#
#             if '$lt:' in fieldV:
#                 ltv = fieldV.replace('$lt:', '')
#                 filder_dict[field] = {'$lt': ltv}
#
#             if '$lte:' in fieldV:
#                 ltev = fieldV.replace('$lte:', '')
#                 filder_dict[field] = {'$lte': ltev}
#
#             if '$regex:' in fieldV:
#                 regexv = fieldV.split(':')
#                 filder_dict[field] = {regexv[0]: regexv[1]}
#
#     # 查询数据
#     count = collecton.count()  # 数据总数
#     data = list(collecton.find(filder_dict, fields, sort=sort_fields).limit(30).skip(int(page) * 30))
#     result = dict()
#     result['fields'] = view.get('fields')
#     result['data'] = data
#     result['count'] = count
#
#     return jsonify({'code': 20000, 'data': result})


@ltscrapyd.route('/notice/linechart')
def spider_notice_linechart():
    parser = reqparse.RequestParser()
    parser.add_argument('begin', type=str, location='values', help='验证错误')
    parser.add_argument('end', type=str, location='values', help='验证错误')
    args = parser.parse_args()

    if not all([args.get('begin'), args.get('end')]):
        begin_date = datetime.now().strftime('%Y-%m-%d 23:59:59')
        end_date = (datetime.now() + timedelta(days=-7)).strftime('%Y-%m-%d 23:59:59')
    else:
        begin_date: str = datetime.strftime(args.get('begin'), '%Y-%m-%d 00:00:00')
        end_date: str = datetime.strftime(args.get('end'), '%Y-%m-%d 23:59:59')

    db = local_mongo.cx['spider_web']
    find_result = db.spider_manage_notice.find({'datetime': {'$gte': end_date, '$lte': begin_date}}, {'_id': 0})

    range_begin_date = datetime.now().strftime("%Y-%m-%d")
    range_end_date = (datetime.now() + timedelta(days=-6)).strftime("%Y-%m-%d")

    date_list: List[str] = [i.strftime('%Y-%m-%d') for i in pd.date_range(start=range_end_date, end=range_begin_date)]
    df = pd.DataFrame(find_result)
    if df.size == 0:
        return jsonify(
            {'code': 20000, 'data': {
                "read_null_count" : 0,
                "error_count_list": [0, 0, 0, 0, 0, 0, 0],
                "info_count_list" : [0, 0, 0, 0, 0, 0, 0],
                "notice_item"     : [],
                "date_list"       : date_list
            }}
        )

    # 未读通知数
    df["date"] = df["datetime"].str.split(expand=True)[0]
    # error数量
    error_count_list = [len(df[(df["date"] == i) & (df["level"] == "error")]) for i in date_list]
    # info数量
    info_count_list = [len(df[(df["date"] == i) & (df["level"] == "info")]) for i in date_list]

    result = {
        "expectedData": error_count_list,
        "actualData"  : info_count_list,
        "xAxisData"   : date_list
    }

    return jsonify(
        {'code': 20000, 'data': result}
    )


@ltscrapyd.route('/notice/unread/count')
def spider_unread_notcie_num():
    db = local_mongo.cx['spider_web']
    unread_count = db.spider_manage_notice.find({'read': False}).count()

    return jsonify(
        {'code': 20000, 'data': unread_count}
    )


class Notice(Resource):
    '''爬虫通知接口，保存异常等一些通知提醒'''
    result_field = {

    }

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=str, location='values', help='验证错误')
        args = parser.parse_args()
        _page = int(args.get('page'))

        db = local_mongo.cx['spider_web']
        _sort = [('read', pymongo.ASCENDING), ('datetime', pymongo.DESCENDING), ('level', pymongo.ASCENDING)]
        find_result = db.spider_manage_notice.find({}, sort=_sort)
        find_result.limit(30).skip(_page * 30)
        result = [i for i in find_result]
        print(result)

        return jsonify(
            {'code': 20000, 'data': result}
        )

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('project', type=str, location='json', help='验证错误')
        parser.add_argument('spider', type=str, default="", location='json', help='验证错误')
        parser.add_argument('title', type=str, location='json', help='验证错误')
        parser.add_argument('content', type=str, location='json', help='验证错误')
        parser.add_argument('level', type=str, location='json', help='验证错误')
        parser.add_argument('from_ip', type=str, location='json', help='验证错误')
        parser.add_argument('datetime', type=str, location='json', help='验证错误')
        parser.add_argument('read', type=str, default=False, location='json', help='验证错误')

        args = dict(parser.parse_args())
        args['_id'] = uuid1().hex

        notice_item = SpiderNotice(**args)
        notice_item.insert('spider_manage_notice')

        return jsonify(
            {'code': 20000}
        )

    def put(self):
        db = local_mongo.cx['spider_web']
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str, location='values', help='验证错误')
        args = parser.parse_args()

        db.spider_manage_notice.update_one({'_id': args.get('id')}, {'$set': {'read': True}})

        return jsonify({'code': 20000})
