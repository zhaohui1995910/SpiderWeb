from . import user, scrapyd, home, spider
from apps.home import home as home_blueprint
from apps.user import user as user_blueprint
from apps.scrapyd import scrapyd as scrapyd_blueprint
from apps.spider import spider as spider_blueprint


def init_app(app):
    app.register_blueprint(home_blueprint, url_prefix='/home')
    app.register_blueprint(user_blueprint, url_prefix='/user')
    app.register_blueprint(scrapyd_blueprint, url_prefix='/scrapyd')
    app.register_blueprint(spider_blueprint, url_prefix='/spider')
