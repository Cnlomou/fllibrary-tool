import requests
import time
import os


class User:
    def __init__(self, phone, password) -> None:
        super().__init__()
        self.phone = phone
        self.password = password
        self.cookie = ''

    def login(self):
        body = {}
        body['uname'] = self.phone
        body['password'] = self.password
        body['refer'] = 'https://office.chaoxing.com/front/third/apps/seat/index?deptIdEnc='
        body['t'] = True
        res = requests.post('https://passport2.chaoxing.com/fanyalogin', body)
        split = res.headers['Set-Cookie'].split(',')
        cookie = ''
        for item in split:
            # s.isdigit()
            if not item.lstrip()[0].isdigit():
                cookie += item.split(';')[0] + ';'
                print('>>>>', item.split(';')[0])
        print(cookie[:len(cookie) - 1])
        self._cookie_cat(cookie[:len(cookie) - 1])

    def sign(self):
        res = self.open("https://office.chaoxing.com/data/apps/seat/reservelist?indexId=0&pageSize=10&type=-1")
        for item in res.json()['data']['reserveList']:
            if item['status'] == 0:
                signres = self.open("https://office.chaoxing.com/data/apps/seat/sign", {'id': item['id']})
                if not bool(signres.json()['success']):
                    raise Exception('签到失败', signres.text)
                print(signres.text)

    def signBack(self):
        res = self.open("https://office.chaoxing.com/data/apps/seat/reservelist?indexId=0&pageSize=10&type=-1")
        for item in res.json()['data']['reserveList']:
            if item['status'] == 1:
                signbackre = self.open("https://office.chaoxing.com/data/apps/seat/signback", {'id': item['id']})
                if not bool(signbackre.json()['success']):
                    raise Exception('签退失败', signbackre.text)
                print(signbackre.text)

    def _cookie_cat(self, cookie):
        if self.cookie:
            self.cookie += '; ' + cookie[:len(cookie) - 1]
        else:
            self.cookie = cookie

    def open(self, url, params=None):
        return requests.get(url, params, headers={'Cookie': self.cookie})


phone = os.getenv("phone", "")
password = os.getenv("passwd", "")
if not phone or not password:
    raise Exception('未配置账号信息')
# "559e6bd2ec45f150e70c4f76764f8770"
print(phone, password)
user = User(phone, password)
user.login()
user.signBack()
