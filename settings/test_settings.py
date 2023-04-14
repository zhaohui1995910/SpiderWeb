from apscheduler.jobstores.redis import RedisJobStore

LOCAL_MONGO_URL = 'mongodb://192.168.125.31:27017'
CLOUD_MONGO_URL = 'mongodb://119.3.20.171:27017'

# cycle 定时任务
SCHEDULER_API_ENABLED = True
SCHEDULER_TIMEZONE = 'Asia/Shanghai'
SCHEDULER_JOBSTORES = {'default': RedisJobStore(host='192.168.125.31', db=1, password='852456')}

# ElasticSearch
ELASTICSEARCH_HOST = ['192.168.125.179']
ELASTICSEARCH_PORT = 9200
ELASTICSEARCH_AUTH_USER = 'elastic'
ELASTICSEARCH_AUTH_PASS = 'changeme'
ELASTICSEARCH_SNIFF_ON_START = False
ELASTICSEARCH_SNIFF_ON_CONNECTION_FAIL = True
ELASTICSEARCH_SNIFFER_TIMEOUT = None

# 登录认证API
AUTH_SIGNIN_URL = "http://192.168.124.60:5000/api/Auth/SignIn"
# 获取用户token
USERINFO_URL = 'http://192.168.124.60:8031/api/services/Foundation/User/GetCurrentUserByAuthToken'
# 获取用户在应用下的权限
PERMISSION_URL = 'http://192.168.124.60:8031/api/services/Foundation/GlobalPermission/LoadUserPermissionsByApplication'
# 业务员是否有客户权限
CUSTOMER_PERMISSION = 'http://192.168.123.218:8000/api/services/Customer/Customer/IsCustomerPermission'
# 通过用户获取客户编码Qcbm
CUSTOMER_LIST = 'http://192.168.123.218:8000/api/services/Customer/Customer/GetCustomerCodeByUser'
