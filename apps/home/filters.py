from flask_restful import fields

sms_list = dict()
sms_list['id'] = fields.String()
sms_list['symbol'] = fields.String()
sms_list['high'] = fields.Float()
sms_list['low'] = fields.Float()
sms_list['decrease'] = fields.Float()
sms_list['increase'] = fields.Float()
sms_list['user_id'] = fields.Integer()
sms_list['notice'] = fields.String()
sms_list['tel'] = fields.String()
