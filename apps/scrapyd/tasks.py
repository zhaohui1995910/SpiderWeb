import time
from copy import deepcopy
from itertools import chain
from datetime import datetime
from dateutil.parser import parse

import gevent
import requests
from scrapyd_api import ScrapydAPI
from bson.objectid import ObjectId

from models import local_mongo
from extension.scheduler import scheduler

taskLock = None


def update_server_table():
    '''更新spider_manage_server表'''
    db = local_mongo.cx['spider_web']
    base_url = 'http://{host}:{port}/daemonstatus.json'
    server_list = db.spider_manage_server.find({})

    for server in server_list:
        auth = (server.get('auth_username'), server.get('auth_password')) if server.get('auth') else None

        url = base_url.format(host=server.get('host'), port=server.get('port'))
        server_info = requests.get(url=url, auth=auth).json()

        update_dict = {
            'status'   : server_info.get('status'),
            'pending'  : server_info.get('pending'),
            'running'  : server_info.get('running'),
            'finished' : server_info.get('finished'),
            'hostName' : server_info.get('node_name'),
            'is_delete': False,
        }
        db.spider_manage_server.update_one(
            {'_id': server.get('_id')},
            {'$set': update_dict}
        )


def update_project_table():
    '''更新spider_manage_project表'''
    db = local_mongo.cx['spider_web']
    base_project_url = 'http://{host}:{port}/listprojects.json'
    base_version_url = 'http://{host}:{port}/listversions.json?project={project}'

    def get_projects(server):
        '''获取项目列表'''
        _project_item_list = []
        url = base_project_url.format(host=server.get('host'), port=server.get('port'))
        auth = (server.get('auth_username'), server.get('auth_password')) if server.get('auth') else None
        project_list = requests.get(url, auth=auth).json().get('projects')
        for project in project_list:
            item = dict()
            item['projectName'] = project
            item['serverAddr'] = server.get('host')
            item['serverPort'] = server.get('port')
            item['hostName'] = server.get('hostName')
            item['auth'] = auth
            _project_item_list.append(deepcopy(item))

        return _project_item_list

    def get_project_version(project):
        '''获取项目版本列表'''
        project_version_item = []
        url = base_version_url.format(
            host=project.get('serverAddr'),
            port=project.get('serverPort'),
            project=project.get('projectName')
        )
        version_list = requests.get(url, auth=project.get('auth', None)).json().get('versions')

        for version in version_list:
            project['version'] = version
            project_version_item.append(deepcopy(project))

        return project_version_item

    def update_project(project):
        '''更新项目列表'''
        project_item = db.spider_manage_project.find_one(
            {
                'name'   : project.get('projectName'),
                'server' : project.get('serverAddr'),
                'port'   : project.get('serverPort'),
                'version': project.get('version'),
            })
        if not project_item:
            db.spider_manage_project.insert_one(
                {
                    'name'       : project.get('projectName'),
                    'server'     : project.get('serverAddr'),
                    'port'       : project.get('serverPort'),
                    'version'    : project.get('version'),
                    'hostName'   : project.get('hostName'),
                    'is_delete'  : False,
                    'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            )

    # 获取服务器列表
    server_list = db.spider_manage_server.find({})
    # 获取项目列表
    project_item_list = list(chain(*[get_projects(server) for server in server_list]))  # chain: 数组降维，二维降到一维
    # 获取每个项目的版本列表
    project_version_item_list = list(chain(*[get_project_version(project) for project in project_item_list]))
    # 更新数据库项目表
    [update_project(project) for project in project_version_item_list]


def update_spider_table():
    '''更新spider_info表'''
    db = local_mongo.cx['spider_web']
    base_project_url = 'http://{host}:{port}/listprojects.json'
    base_version_url = 'http://{host}:{port}/listversions.json?project={project}'
    base_spider_url = 'http://{host}:{port}/listspiders.json?project={project}&_version={version}'

    def get_projects(server):
        '''获取项目列表'''
        _project_item_list = []
        project_list = requests.get(base_project_url.format(
            host=server.get('host'),
            port=server.get('port'))
        ).json().get('projects')
        for project in project_list:
            item = dict()
            item['projectName'] = project
            item['serverAddr'] = server.get('host')
            item['serverPort'] = server.get('port')
            _project_item_list.append(deepcopy(item))
        return _project_item_list

    def get_project_version(project):
        '''获取项目版本列表'''
        project_version_item = []
        url = base_version_url.format(
            host=project.get('serverAddr'),
            port=project.get('serverPort'),
            project=project.get('projectName')
        )
        version_list = requests.get(url).json().get('versions')
        for version in version_list:
            project['version'] = version
            project_version_item.append(deepcopy(project))
        return project_version_item

    def get_update_spiders(project, version):
        '''获取爬虫列表，并更新数据库'''
        url = base_spider_url.format(
            host=project.get('serverAddr'),
            port=project.get('serverPort'),
            project=project.get('projectName'),
            version=version
        )

        spiders = requests.get(url).json().get('spiders', [])

        for spider in spiders:
            spider_item = db.spider_manage_spider.find_one(
                {
                    'project': project.get('projectName'),
                    'version': project.get('version'),
                    'name'   : project.get(spider)
                }
            )
            if not spider_item:
                db.spider_manage_spider.insert_one(
                    {
                        'name': ''
                    }
                )

    def update_spider(project):
        for version in project.get('version'):
            get_update_spiders(project, version)

    # 获取服务器列表
    server_list = db.spider_manage_server.find({})
    # 获取项目列表
    project_item_list = list(chain(*[get_projects(s) for s in server_list]))
    # 获取每个项目的版本列表
    project_version_item_list = list(chain(*[get_project_version(p) for p in project_item_list]))

    spawns = [gevent.spawn(update_spider, project) for project in project_version_item_list]
    gevent.joinall(spawns)


def update_spider_job():
    '''更新jobs列表'''
    db = local_mongo.cx['spider_web']
    job_list = db.spider_manage_job.find(
        {
            'status'   : {'$ne': 'finished'},
            'is_delete': False
        }
    )

    for job in job_list:
        # 获取scrapyd中 项目的job列表
        scrapyd_job_list = scrapyd_listjobs(
            host=job.get('server'),
            port=job.get('port'),
            project=job.get('project')
        )

        for runJob in scrapyd_job_list.get('running'):
            if runJob.get('id') == job.get('job'):
                now_time = datetime.now()
                start_time = parse(runJob.get('start_time').split('.')[0])
                runtime = now_time - start_time
                days = runtime.days
                hours, remainder = divmod(runtime.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                db.spider_manage_job.update_one(
                    {
                        '_id': job.get('_id')
                    },
                    {
                        '$set': {
                            'status'    : 'running',
                            'start_time': runJob.get('start_time').split('.')[0],
                            'days'      : runtime.days,
                            'runtime'   : f'{days}:{hours}:{minutes}.{seconds}'
                        }
                    }
                )

        for finisJob in scrapyd_job_list.get('finished'):
            if finisJob.get('id') == job.get('job'):
                start_time = parse(finisJob.get('start_time').split('.')[0])
                finish_time = parse(finisJob.get('end_time').split('.')[0])
                runtime = finish_time - start_time
                days = runtime.days
                hours, remainder = divmod(runtime.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                db.spider_manage_job.update_one(
                    {
                        '_id': job.get('_id')
                    },
                    {
                        '$set': {
                            'status'     : 'finished',
                            'start_time' : finisJob.get('start_time').split('.')[0],
                            'finish_time': finisJob.get('end_time').split('.')[0],
                            'runtime'    : f'{days}:{hours}:{minutes}.{seconds}'
                        }
                    }
                )
        # 更新任务的请求数和item数
        log_json = scrapyd_logs(
            host=job.get('server'),
            port=job.get('port'),
            project=job.get('project'),
            spider=job.get('spider'),
            log_nmae=job.get('job')
        )
        update_dict = {
            'pages'      : log_json.get('pages') if log_json.get('pages') else 0,
            'items'      : log_json.get('items') if log_json.get('items') else 0,
            'datas'      : str(log_json.get('datas')),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        db.spider_manage_job.update_one(
            {'_id': job.get('_id')},
            {'$set': update_dict}
        )


def start_job_task(task_id):
    '''taskId: type str'''
    db = local_mongo.cx['spider_web']
    task_item = db.spider_manage_task.find_one(
        {'_id': ObjectId(task_id)}
    )
    # 保存爬虫运行记录
    job = {
        'project'   : task_item.get('project'),
        'server'    : task_item.get('server'),
        'port'      : task_item.get('port'),
        'spider'    : task_item.get('spider'),
        'version'   : task_item.get('version'),
        'status'    : 'pending',
        'is_delete' : False,
        'job'       : task_item.get('name') + '_' + str((task_item.get('run_count', 0) + 1)),
        'start_time': task_item.get('next_run_time'),
        'taskId'    : task_id
    }
    # 启动爬虫job
    schedule_job(task=task_item, job=job)
    # 添加到数据库
    db.spider_manage_job.insert_one(job)
    task_job = scheduler.get_job(id=task_item.get('name'))
    # 更新task参数
    task_update = {
        'run_count'    : task_item.get('run_count') + 1,
        'prev_run_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
        'next_run_time': task_job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
    }
    db.spider_manage_task.update_one(
        {'_id': ObjectId(task_id)},
        {'$set': task_update}
    )


def schedule_job(task, job):
    '''启动爬虫'''
    db = local_mongo.cx['spider_web']
    item = db.spider_manage_server.find_one(
        {
            'host': task.get('server'),
            'port': task.get('port')
        }
    )

    host, port = item.get('host'), item.get('port')
    target = f'http://{host}:{port}'

    auth = (item.get('auth_username'), item.get('auth_password')) if item.get('auth') else None
    scrapy_api = ScrapydAPI(target=target, auth=auth, timeout=10)

    # 获取settings配置
    settings = task.get('settings')
    additional = settings.pop('additional', '')

    additional_result = {}
    for item in additional.split('&'):
        if item and '=' in item:
            key, value = item.split('=')
            additional_result[key] = value

    for i, v in settings.items():
        if v is not None and v != '':
            settings[i] = v

    # 请求启动爬虫
    job_id = scrapy_api.schedule(
        project=task.get('project'),
        spider=task.get('spider'),
        jobid=job.get('job'),
        _version=task.get('version'),
        settings=settings,
        **additional_result
    )
    return job_id


def scrapyd_listjobs(host, port, project):
    '''获取项目jobs'''
    db = local_mongo.cx['spider_web']
    item = db.spider_manage_server.find_one(
        {
            'host': host,
            'port': port
        }
    )

    url = f'http://{host}:{port}/listjobs.json?project={project}'

    auth = (item.get('auth_username'), item.get('auth_password')) if item.get('auth') else None

    result = requests.get(url=url, auth=auth).json()

    return result


def scrapyd_logs(host, port, project, spider, log_nmae):
    '''获取json日志'''
    db = local_mongo.cx['spider_web']
    item = db.spider_manage_server.find_one(
        {
            'host': host,
            'port': port
        }
    )

    url = f'http://{host}:{port}/logs/{project}/{spider}/{log_nmae}.json'

    auth = (item.get('auth_username'), item.get('auth_password')) if item.get('auth') else None

    result = requests.get(url=url, auth=auth)

    if result.status_code != 200:
        return {}

    return result.json()
