from flask import Blueprint
from flask_restful import Api

spider = Blueprint('spider', __name__)
api = Api(spider)
