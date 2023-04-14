from . import scheduler, celery, cors, cache


def init_app(app):
    # 配置 apscheduler
    scheduler.init_scheduler(app)
    # 配置celery
    celery.init_celery(app)
    # 配置CSRF
    cors.init_cors(app)
    # 配合cache缓存
    cache.init_cache(app)


