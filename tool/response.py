from flask import jsonify


def make_result(resultcode, message='', error_code=1, data=False):
    if data is False:
        return dict(resultcode=resultcode, message=message, error_code=error_code)

    return jsonify(dict(resultcode=resultcode, data=data, message=message, error_code=error_code))


class ErrorResponse(object):
    @staticmethod
    def result(resultcode, reason):
        return make_result(resultcode=resultcode, message=reason)

    @staticmethod
    def error_500(error):
        return jsonify(make_result(resultcode=200, message='服务器错误'))

    @staticmethod
    def error_404(error):
        return jsonify(make_result(resultcode=200, message='检查路由地址'))

    @staticmethod
    def error_scrapyd():
        return jsonify(make_result(resultcode=60001, message='请求scrapyd异常'))


class SuccessResponse(object):
    @staticmethod
    def result(resultcode, data, reason=''):
        return make_result(resultcode=resultcode, message=reason, error_code=0, data=data)
