import requests
from flask import jsonify, request, current_app
from flask_restful import Resource


class UserInfo(Resource):

    def get(self):
        """获取渠成用户信息"""
        token = request.headers.get('X-Token')
        # 1 请求渠成认证接口，获取用户信息
        response = requests.get(
            url=current_app.config.get('USERINFO_URL'),
            headers={'Authorization': token})
        result_json = response.json()
        user_info: dict = result_json.get('result', {})

        # 2 请求渠成权限中心，获取用户权限列表
        response = requests.post(
            url=current_app.config.get('PERMISSION_URL'),
            headers={'Authorization': token},
            json={
                "applicationName": "Spider",
                "moduleName"     : "string",
                "specUserName"   : user_info['userName']
            })
        result_json = response.json()
        items = result_json.get('result').get('items')
        permission: list = [i['name'] for i in items]

        # 3 构建用户信息（user_info)
        user = dict()
        user['roles'] = permission
        user['introduction'] = ''
        user['avatar'] = '/static/img/admin-header.jpg'
        user['name'] = user_info['displayName']

        return jsonify({'code': 20000, 'data': user})


class UserLogout(Resource):

    def post(self):
        return {'code': 20000, 'data': 'success'}


class UserSignin(Resource):

    def post(self):

        username = request.json.get('username')
        password = request.json.get('password')

        status, result = self.get_token(username, password)

        if status:
            return jsonify({'code': 20000, 'data': {'token': result}})
        else:
            return jsonify({'code': 60204, 'message': 'Login failure; token: %s' % result})

    def get_token(self, username, password):

        data = {
            "clientId"    : "Default",
            "clientSecret": "erp_secret",
            "signName"    : username,
            "password"    : password
        }
        auth_url = current_app.config.get('AUTH_SIGNIN_URL')
        response = requests.post(url=auth_url, json=data)

        if response.status_code != 200:
            return False, '认证失败'

        result_json = response.json()
        if result_json.get('success'):
            access_token = result_json.get('data', {}).get('access_token')
            return True, access_token
        else:
            result = result_json.get('result')
            return False, result
