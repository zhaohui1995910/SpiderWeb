from flask_restful import fields

server = {
    'host'        : fields.String,
    'port'        : fields.String,
    'auth'        : fields.Boolean,
    'authUsername': fields.String,
    'authPassword': fields.String,
    'hname'       : fields.String
}
