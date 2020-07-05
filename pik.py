import requests
import json
import os
import time
from helpers import hash_vals, dump_data, load_data, compare


class PIKData(object):

    def __init__(self, login, password, data_dir='data'):
        self.sess = requests.Session()
        self.login = login
        self.password = password
        self.data_dir = data_dir
        self.data_uri = 'https://api.pik.ru/v1/opportunity/log?opportunity_id={}'
        self.auth_uri = 'https://api.pik.ru/v1/auth'
        self.appointment_uri = 'https://api.pik.ru/v1/office/appointment'
        self.token_path = os.path.join(self.data_dir, 'token.json')
        self.token = self.get_token(login, password)

        # Добавляем куку и заголовок с токеном
        self.sess.headers = {
            'TOKEN': self.token,
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0',
            'Referer': 'https://pik.ru',
            'Origin': 'https://pik.ru'
        }
        cookie_obj = requests.cookies.create_cookie(name='PIK_TOKEN',
                                                    value=self.token)
        self.sess.cookies.set_cookie(cookie_obj)
        # Получаем айдишники квартиры и договора
        self.get_flat_data()
        # Получаем этапы выполнения договора
        self.progress = self.get_progress()
        # Получаем данные раздела сопровождения
        self.appointment = self.get_appointment()
        # Получаем поле статуса этапа "Получение ключей"
        self.keys_status = self.progress[5]

    def get_token(self, login=None, password=None):
        if not login:
            login = self.login
        if not password:
            password = self.password

        old_token = load_data(self.token_path)
        expiration = old_token.get('expires_in', old_token.get('expiresIn', time.time()))
        diff = expiration - time.time()
        if diff <= 518400:
            print('Обновление токена')
            try:
                token = self.refresh_token(login, password)
            except:
                print('Обновление токена не удалось')
                token = old_token['token']
        else:
            token = old_token['token']
        return token

    def refresh_token(self, login, password):
        request = {"login": login, "password": password}
        response = self.sess.post(url=self.auth_uri, json=request)
        dump_data(response.json(), self.token_path)
        token = response.json()['token']
        return token

    def get_flat_data(self):
        page = self.sess.get('https://www.pik.ru/client/property').content.decode()
        data_raw = page.split('<script id="__NEXT_DATA__" type="application/json">')[-1].split('</script>')[0]
        data = json.loads(data_raw)['props']['initialState']['dealsService']['deals']
        for e in data:
            if data[e]['isFlat'] == True:
                self.oid = data[e]['deal']['id']
                self.flat_id = data[e]['guid']
                self.flat_data = data[e]
                self.flat_data.pop('flats')

    def get_progress(self):
        response = self.sess.get(url=self.data_uri.format(self.oid)).json()
        return response

    def get_appointment(self):
        response = self.sess.post(url=self.appointment_uri, json={'flat_id': self.flat_id}).json()
        return response
