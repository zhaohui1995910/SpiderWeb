from flask_cors import *


def init_cors(app):
    cors = CORS(app=app, upports_credentials=True)
    return cors
