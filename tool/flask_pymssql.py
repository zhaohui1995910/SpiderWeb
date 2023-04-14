# -*- coding: utf-8 -*-
# @Time    : 2021/9/2 16:27
# @Author  : 10867
# @FileName: flask_pymssql.py
# @Software: PyCharm
import pymssql


class FlaskPymssql:
    def __init__(self):
        self.conn = None

    def init_app(self, app):
        self.conn = pymssql.connect(
            server=app.config.get('MSSQL_SERVER'),
            user=app.config.get('MSSQL_USER'),
            password=app.config.get('MSSQL_PASSWORD'),
            database=app.config.get('MSSQL_DATABASE'),
            charset='GB2312'
        )

    @property
    def cursor(self):
        return self.conn.cursor(as_dict=True)

    def __getattr__(self, item):
        return getattr(self.conn, item)


class DBConnection(object):
    def __init__(self, ip, user, passwd, db):
        self.server = ip
        self.user = user
        self.password = passwd
        self.database = db
        self.charset = 'utf8'

        self.conn = None
        self.cur = None

    def connect(self):
        if self.conn:
            return self.conn

        self.conn = pymssql.connect(
            server=self.server,
            user=self.user,
            password=self.password,
            database=self.database,
            charset=self.charset
        )
        return self.conn

    def __enter__(self):
        if self.conn:
            self.cur = self.conn.cursor(as_dict=True)
            return self.cur

        self.conn = pymssql.connect(
            server=self.server,
            user=self.user,
            password=self.password,
            database=self.database,
            charset=self.charset
        )
        self.cur = self.conn.cursor(as_dict=True)
        return self.cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cur.close()
        self.conn.close()
