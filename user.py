import re
import datetime
from dateutil.relativedelta import relativedelta
import time
import os
import requests
import json


class Verifier:
    def __init__(self, cookie) -> None:
        super().__init__()
        self.token = ''
        self.url = "https://captcha.chaoxing.com/captcha/get/verification/image"
        self.params = dict()
        self.params["callback"] = "jQuery33107621268123806113_166549880084"
        self.params["captchaId"] = "42sxgHoTPTKbt0uZxPJ7ssOvtXr3ZgZ1"
        self.params['type'] = 'slide'
        self.params['version'] = '1.1.11'
        self.cookie = str(cookie)
        self.third_part_token = os.getenv("api_token", "")
        self.headers = {
            'Accept': '*/*',
            'User-Agent': 'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12F70 Safari/600.1.4'}

    def validate(self):
        response = requests.get(self.url, self.params, headers={'Cookie': self.cookie})
        if 'Set-Cookie' in response.headers:
            setcookie = response.headers['Set-Cookie']
            self.cookie += '; ' + setcookie[:setcookie.find(';')]
        dic = self._jsoup_to_dict(response.text)
        print(dic['token'])
        slidesets = dic['imageVerificationVo']
        x = self._request_verify_api_slide(slidesets['shadeImage'], slidesets['cutoutImage'])
        return self._check_verification(json.dumps([{'x': int(x)}]), dic['token'])

    def _jsoup_to_dict(self, text: str):
        l = text.find('(')
        r = text.find(')')
        print(text[l + 1:r])
        if l < 0 or l >= r:
            return ''
        return json.loads(text[l + 1:r], encoding='utf-8')

    def _request_verify_api_slide(self, image, slide):
        res = requests.post("https://www.jfbym.com/api/YmServer/customApi",
                            {"type": 20111, "slide_image": slide, "background_image": image,
                             "token": self.third_part_token})
        print(res.text)
        return res.json()['data']['data']

    def _check_verification(self, location, token):
        print(f"check location >>{location},token>> {token}")
        l_params = {}
        l_params['callback'] = "jQuery33108903501503446305_1665586321782"
        l_params['captchaId'] = '42sxgHoTPTKbt0uZxPJ7ssOvtXr3ZgZ1'
        l_params['textClickArr'] = location
        l_params['coordinate'] = '[]'
        l_params['runEnv'] = '10'
        l_params['version'] = '1.1.11'
        l_params['token'] = token
        l_params['type'] = 'slide'
        l_params['_'] = int(time.time() * 1000)
        h = dict(self.headers)
        h['Cookie'] = self.cookie
        h['Referer'] = "https://office.chaoxing.com/"
        checkres = requests.get(
            'https://captcha.chaoxing.com/captcha/check/verification/result',
            l_params, headers=h)
        print('check response: ', checkres.text)
        verification_res = self._jsoup_to_dict(checkres.text)
        if verification_res['result']:
            return json.loads(verification_res['extraData'])['validate']
        raise Exception('验证错误')


class User:
    def __init__(self, phone, password) -> None:
        super().__init__()
        self.phone = phone
        self.password = password
        self.cookie = ''
        self.verifier: Verifier = Verifier(self)
        self.isLogin = False
        self.headers = {
            'Accept': '*/*',
            'User-Agent': 'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12F70 Safari/600.1.4'}

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
        self.isLogin = True

    def _ensure(self):
        if not self.isLogin:
            raise Exception("请先进行登录")

    def sign(self):
        self._ensure()
        res = self.open("https://office.chaoxing.com/data/apps/seat/reservelist?indexId=0&pageSize=10&type=-1")
        for item in res.json()['data']['reserveList']:
            if item['status'] == 0 and item['type'] == -1:
                signres = self.open("https://office.chaoxing.com/data/apps/seat/sign", {'id': item['id']})
                if not bool(signres.json()['success']):
                    raise Exception('签到失败', signres.text)
                print(signres.text)

    def signBack(self):
        self._ensure()
        res = self.open("https://office.chaoxing.com/data/apps/seat/reservelist?indexId=0&pageSize=10&type=-1")
        for item in res.json()['data']['reserveList']:
            if item['status'] == 1 and item['type'] == -1:
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

    def today(self, offset=0):
        now = datetime.datetime.now()
        nnow = now + relativedelta(day=now.day + offset)
        return nnow.strftime('%Y-%m-%d')

    def seat_submit(self, day, seatNum, startTime, endTime):
        self._ensure()
        lparams = {}
        lparams['roomId'] = 8197
        lparams['startTime'] = startTime
        lparams['endTime'] = endTime
        lparams['day'] = day
        lparams['captcha'] = self.verifier.validate()
        lparams['seatNum'] = seatNum
        lparams['token'] = self._parse_submit_token(day, seatNum)
        self.headers['Cookie'] = self.cookie
        res = requests.get("https://office.chaoxing.com/data/apps/seat/submit", lparams, headers=self.headers)
        print(res.text)

    def _parse_submit_token(self, day, seatNum):
        lparams = {}
        lparams['id'] = 8197
        lparams['day'] = day
        lparams['seatNum'] = seatNum
        lparams['backLevel'] = 1
        lparams['pageToken'] = self._getPageToken()
        res = requests.get("https://office.chaoxing.com/front/third/apps/seat/select", lparams,
                           headers={'Cookie': self.cookie})
        reg = r"token = '\w*'"
        search = re.search(reg, res.text)
        if search:
            group = search.group(0)
            token = group[group.rfind("'", 0, len(group) - 1) + 1:len(group) - 1]
            print("token >>", token)
            return token
        raise Exception('获取token时失败')

    def _getPageToken(self):
        res = requests.get('https://office.chaoxing.com/front/third/apps/seat/index?deptIdEnc=', None,
                           headers={'Cookie': self.cookie})
        reg = r"(pageToken=' \+ '\w*')"
        re_compile = re.compile(reg).search(res.text)
        if re_compile:
            group = re_compile.group(0)
            page_token = group[group.rfind("'", 0, len(group) - 1) + 1:len(group) - 1]
            print("pageToken>>", page_token)
            return page_token
        else:
            raise Exception("获取pathToken时失败")


phone = os.getenv("phone", "")
password = os.getenv("passwd", "")
arg = int(os.getenv('arg', '-1'))
if not phone or not password:
    raise Exception('未配置账号信息')
# "559e6bd2ec45f150e70c4f76764f8770"
# print(phone, password)
user = User(phone, password)
user.login()
if arg == 1:
    user.sign()
elif arg == 2:
    user.signBack()
