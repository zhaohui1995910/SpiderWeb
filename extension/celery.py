from celery import Celery


def init_celery(app):
    celery = Celery(app.name)
    celery.conf.update(app.config)
    return celery
