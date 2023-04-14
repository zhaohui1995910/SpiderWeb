import os
import logging
from logging import handlers

from flask import Flask
from dotenv import load_dotenv

import models
import routes
import extension
from tool.response import ErrorResponse


def create_app():
    app = Flask(__name__)
    # 配置文件
    add_config(app)
    # 添加拓展
    add_extensions(app)
    # 添加日志
    add_logger(app)
    # 定义错误返回
    add_errorheaders(app)

    return app


def add_config(app):
    """加载配置"""
    load_dotenv('.env', override=False)
    app.config.from_pyfile('./settings/settings.py', silent=True)
    app.config.from_pyfile(f"./settings/{os.environ.get('FLASK_ENV')}_settings.py", silent=True)


def add_logger(app):
    logging_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s'
    )
    handler = handlers.TimedRotatingFileHandler(
        "logs/log.log",
        when="D",
        interval=1,
        backupCount=15,
        encoding="UTF-8",
        delay=False,
        utc=True
    )
    handler.setFormatter(logging_format)
    handler.setLevel(logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)


def add_extensions(app):
    # 注册model
    models.init_app(app)
    # 注册路由
    routes.init_app(app)
    # 注册扩展
    extension.init_app(app)


def add_errorheaders(app):
    """定义错误响应"""
    app.register_error_handler(500, ErrorResponse.error_500)
    app.register_error_handler(404, ErrorResponse.error_404)


app = create_app()

if __name__ == '__main__':
    app.run()
