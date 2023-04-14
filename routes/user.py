from apps.user import api
from apps.user import views

api.add_resource(views.UserInfo, '/info')
api.add_resource(views.UserLogout, '/logout')
api.add_resource(views.UserSignin, '/signin')
