from datetime import datetime
from typing import List
from dataclasses import dataclass, field

from . import BaseMongoModels


@dataclass
class ServerModel(BaseMongoModels):
    _id: str = field(default='')
    host: str = field(default='')
    port: str = field(default='')
    auth: bool = field(default=False)
    auth_username: str = field(default='')
    auth_password: str = field(default='')
    finished: int = field(default=0)
    hostName: str = field(default='')
    pending: int = field(default=0)
    running: int = field(default=0)
    status: str = field(default='')
    is_delete: bool = field(default=False)


@dataclass
class ProjectModel(BaseMongoModels):
    _id: str = field(default='')
    name: str = field(default='')
    port: str = field(default='')
    server: str = field(default='')
    version: str = field(default='')
    hostName: str = field(default='')
    is_delete: bool = field(default=False)


@dataclass
class SpiderModel(BaseMongoModels):
    _id: str = field(default='')
    name: str = field(default='')
    desc: str = field(default='')
    project: str = field(default='')
    server: str = field(default='')
    port: str = field(default='')
    version: str = field(default='')
    views: bool = field(default=False)


@dataclass
class JobModel(BaseMongoModels):
    _id: str = field(default='')
    project: str = field(default='')
    server: str = field(default='')
    port: str = field(default='')
    spider: str = field(default='')
    version: str = field(default='')
    status: str = field(default='')
    is_delete: bool = field(default=False)
    job: str = field(default='')
    start_time: str = field(default='')
    taskId: str = field(default='')
    days: int = field(default=None)
    runtime: str = field(default='')
    finish_time: str = field(default='')
    datas: str = field(default='')
    items: int = field(default=0)
    pages: int = field(default=0)
    update_time: str = field(default='')


@dataclass
class TaskModel(BaseMongoModels):
    _id: str = field(default='')
    status: bool = field(default=False)
    trigger: str = field(default='')
    run_count: int = field(default=0)
    server: str = field(default='')
    port: str = field(default='')
    project: str = field(default='')
    version: str = field(default='')
    spider: str = field(default='')
    name: str = field(default='')
    settings: dict = field(default_factory={})
    timer: dict = field(default_factory={})
    next_run_time: str = field(default='')
    prev_run_time: str = field(default='')


@dataclass
class DataViewsModel(BaseMongoModels):
    _id: str = field(default='')

    name: str = field(default='')
    desc: str = field(default='')
    db: str = field(default='')
    table: str = field(default='')
    fields: List[str] = field(default_factory=[])
    # spider
    project: str = field(default='')
    spider: str = field(default='')
    version: str = field(default='')

    create_time: str = field(default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@dataclass
class SpiderNotice(BaseMongoModels):
    '''爬虫通知'''
    _id: str = field(default='')

    project: str = field(default='')
    spider: str = field(default='')

    title: str = field(default='')
    content: str = field(default='')
    level: str = field(default='')
    from_ip: str = field(default='')
    datetime: str = field(default='')
    read: bool = field(default=False)  # 已读标记


__all__ = [
    'ServerModel',
    'ProjectModel',
    'SpiderModel',
    'JobModel',
    'TaskModel',
    'DataViewsModel',
    'SpiderNotice'
]
