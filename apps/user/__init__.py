from flask import Blueprint
from flask_restful import Api

user = Blueprint('user', __name__)
api = Api(user)
