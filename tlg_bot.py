import telegram

from flatten_dict import flatten
import os
import time
import datetime

from pik import PIKData
from helpers import hash_vals, dump_data, load_data, compare

class Credentials(object):
    def __init__(self, credentials_json):
        self.__credentials = load_data(credentials_json)
        self.auth_token = self.__get_param('TLG_TOKEN', 'auth_token')
        self.chat_id = self.__get_param('TLG_CHAT_ID', 'chat_id')
        self.login = self.__get_param('PIK_LOGIN', 'pik_login')
        self.password = self.__get_param('PIK_PASSWORD', 'pik_password')

    def __get_param(self, ENV, key):
        return os.environ.get(ENV, self.__credentials.get(key))


class TelegramSender(object):

    def __init__(self, auth_token, chat_id, data_dir='data'):
        self.tpath = os.path.join(data_dir, 'timemsg.json')
        self.auth_token = auth_token
        self.chat_id = chat_id
        self.bot = telegram.Bot(self.auth_token)

    def send_message(self, data):
        template = '<b>Обнаружены изменения в личном кабинете!</b>\n'
        for e in data:
            template += '\nРаздел <b>"{}":</b>\n'.format(e['label'])
            for val in e['values']:
                template += '    <i>{}</i>\n'.format(val)
        resp = self.bot.send_message(self.chat_id, template, parse_mode='html')
        print(resp)

    def send_init_message(self, data):
        template = '<b>Инициализация мониторинга.</b>\n'
        for e in data:
            template += '\nСканирование раздела <b>"{}"...</b>\n'.format(e['label'])
            vals = len(e['values'])
            template += '  Обнаружено <b>{}</b> параметров для отслеживания.'.format(vals)
            template += '\n'
        resp = self.bot.send_message(self.chat_id, template, parse_mode='html')
        print(resp)

    def send_time_message(self, template):
        timemsg = load_data(self.tpath)
        data = self.bot.send_message(self.chat_id, template, disable_notification=True)
        mid = data['message_id']
        timemsg[self.chat_id] = mid
        dump_data(timemsg, self.tpath)

    def update_time_message(self):
        id = load_data(self.tpath).get(self.chat_id)
        template = "Последняя проверка:\n{}".format((datetime.datetime.now().strftime("%d %b %H:%M:%S")))
        if id:
            self.bot.editMessageText(template, self.chat_id, id)
        else:
            self.send_time_message(template)

class Checker(object):
    steps = [
        {'label': 'Мои объекты/Главное',
         'params': {
             'new_data': 'flat_data',
             'file': 'flat.json'
         }
         },
        {'label': 'Мои объекты/Ход сделки/Выдача ключей',
         'params': {
             'new_data': 'keys_status',
             'file': 'progress.json'
         }
         },
        {'label': 'Сопровождение',
         'params': {
             'new_data': 'appointment',
             'file': 'appointment.json'
         }
         },
    ]

    def __init__(self,credentials, folder = 'data', silent = True):
        self.credentials = credentials
        self.silent = silent
        self.folder = folder
        self.bot = TelegramSender(self.credentials.auth_token, self.credentials.chat_id, folder)

    def check(self):
        # Логинимся и получаем данные
        pik_data = PIKData(self.credentials.login, self.credentials.password)
        changes = []
        init = False
        for step in self.steps:
            try:
                params = step['params']
                label = step['label']
                print("Проверка '{}':".format(label))
                path = os.path.join(folder, params['file'])

                initial_data = flatten(load_data(path), reducer='dot')
                new_data = flatten(getattr(pik_data, params['new_data']), reducer='dot')

                if not initial_data:
                    init = True
                diffs = compare(initial_data, new_data)
                if diffs:
                    print('Обнаружены изменения!')
                    print(diffs)
                    changes.append({'label': label, 'values': diffs})
                    # dump_data(params['new_data'], path)
                else:
                    print('    Изменений нет!')
            except Exception as e:
                print('Exception:', str(e))
        if changes and not self.silent:
            if init:
               self.bot.send_init_message(changes)
            else:
               self.bot.send_message(changes)
        if not self.silent:
            self.bot.update_time_message()

if __name__ == '__main__':

    folder = os.environ.get('DATA_DIR', 'data')
    mode = os.environ.get('MODE', 'single')
    delay = int(os.environ.get('DELAY', 600))
    credentials_json = os.path.join(folder, 'credentials.json')

    credentials = Credentials(credentials_json)
    checker = Checker(credentials, folder, silent = False)

    if mode == 'single':
        checker.check()
        print("Wait {} sec.".format(delay))
        time.sleep(delay)
    elif mode == 'loop':
        while True:
            checker.check()
            print("Wait {} sec.".format(delay))
            time.sleep(delay)

