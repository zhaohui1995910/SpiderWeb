from flask_apscheduler import APScheduler

scheduler = APScheduler()


def init_scheduler(app):
    scheduler.init_app(app)
    scheduler.start()
    # 初始化 tasks
    from apps.scrapyd import tasks

    if not scheduler.get_job('scrapyd_server_engine'):
        scheduler.add_job(
            'scrapyd_server_engine',
            tasks.update_server_table,
            trigger='interval',
            seconds=30
        )
    if not scheduler.get_job('scrapyd_project_engine'):
        scheduler.add_job(
            'scrapyd_project_engine',
            tasks.update_project_table,
            trigger='interval',
            seconds=30
        )
    if not scheduler.get_job('scrapyd_job_engine'):
        scheduler.add_job(
            'scrapyd_job_engine',
            tasks.update_spider_job,
            trigger='interval',
            seconds=30
        )
