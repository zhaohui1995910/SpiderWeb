from flask import Blueprint
from flask_restful import Api

home = Blueprint('home', __name__)
api = Api(home)

from . import views
