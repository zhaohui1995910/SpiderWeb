import requests
from fake_useragent import UserAgent


class User_Agent(UserAgent):
    """UserAgent"""

    def __init__(self):
        super(User_Agent, self).__init__(verify_ssl=False)

    def random(self):
        '''随机获取一个useragent'''
        headers = {'User-Agent': self.__getattr__('random')}
        return headers


class Cookiesjar():
    cookies = {'xq_r_token': '29fe5e93ec0b24974bdd382ffb61d026d8350d7d',
               'xq_a_token': '75661393f1556aa7f900df4dc91059df49b83145'}

    def xueqiu_update(self):
        '''登录获取cookeis'''
        url = 'https://xueqiu.com/'
        response = requests.get(url, headers=User_Agent().random())
        xuqiu_cookies = dict(response.cookies.items())
        self.cookies['xq_r_token'] = xuqiu_cookies.get('xq_r_token', '')
        self.cookies['xq_a_token'] = xuqiu_cookies.get('xq_a_token', '')
        return self.cookies


Useragent = User_Agent()
Cookies = Cookiesjar()

if __name__ == '__main__':
    print(Cookies.xueqiu_update())
