from flask import Blueprint
from flask_restful import Api

scrapyd = Blueprint('scrapyd', __name__)
api = Api(scrapyd)
