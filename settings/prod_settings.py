from apscheduler.jobstores.redis import RedisJobStore

LOCAL_MONGO_URL = 'mongodb://192.168.125.115:27017'
SPIDER_MONGO_URL = 'mongodb://lumi:lumi2021@192.168.125.31:27018'

# cycle 定时任务
SCHEDULER_API_ENABLED = True
SCHEDULER_TIMEZONE = 'Asia/Shanghai'
SCHEDULER_JOBSTORES = {'default': RedisJobStore(password=195910, db=2, host='192.168.125.115')}

LUMI_API_SERVER = 'http://192.168.124.60:5000'

# 登录认证API
AUTH_SIGNIN_URL = 'http://192.168.123.214:5000/api/Auth/SignIn'
# 获取用户token
USERINFO_URL = 'http://192.168.123.70:8031/api/services/Foundation/User/GetCurrentUserByAuthToken'
# 获取用户在应用下的权限
PERMISSION_URL = 'http://192.168.123.70:8031/api/services/Foundation/GlobalPermission/LoadUserPermissionsByApplication'
# 业务员是否有客户权限
CUSTOMER_PERMISSION = 'http://192.168.123.218:8000/api/services/Customer/Customer/IsCustomerPermission'
# 通过用户获取客户编码Qcbm
CUSTOMER_LIST = 'http://192.168.123.218:8000/api/services/Customer/Customer/GetCustomerCodeByUser'

# ElasticSearch
ELASTICSEARCH_HOST = ['192.168.123.60', '192.168.123.61', '192.168.123.62', '192.168.123.65']
ELASTICSEARCH_PORT = 9200
ELASTICSEARCH_AUTH_USER = 'elastic'
ELASTICSEARCH_AUTH_PASS = 'changeme'
ELASTICSEARCH_SNIFF_ON_START = False
ELASTICSEARCH_SNIFF_ON_CONNECTION_FAIL = True
ELASTICSEARCH_SNIFFER_TIMEOUT = None

# SqlServer数据库
MSSQL_SERVER = '192.168.123.220:1433'
MSSQL_USER = 'spider'
MSSQL_PASSWORD = 'spider2020'
MSSQL_DATABASE = 'spider'
