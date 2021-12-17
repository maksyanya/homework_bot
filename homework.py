import exceptions
import logging
import os
import requests
import time

from dotenv import load_dotenv
from telegram import Bot


STATUS = 'Изменился статус проверки работы "{name}". {verdict}'
TOKENS_ERROR = 'Отсутствующие токены {token}'
PATH = 'C:/Users/User/OneDrive/Dev/homework_bot/'
TOKENS = ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID')
BOT_WORKING = 'Бот работает'
FAULT_TOKENS = "Ошибка токенов"
MESSAGE = 'Сбой в работе программы: {faults}'
ERROR = 'Произошла ошибка {fault}.'
CODE_ERROR = 'Код ошибки:{key}. Код статуса:{state}'
ERROR_API = 'Ошибка при запросе к API Yandex. Код-возврата:{state}'

load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def get_api_answer(current_timestamp):
    """Делается запрос к эндпоинту API-сервиса."""
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
    except Exception as error:
        logging.error(ERROR.format(fault=error))
    response_json = homework_statuses.json()
    status = homework_statuses.status_code
    if status != 200:
        if ['code'] in response_json:
            code = response_json['code']
            logging.error(CODE_ERROR.format(key=code, state=status))
        if ['error'] in response_json:
            code = response_json['error']
            logging.error(CODE_ERROR.format(key=code, state=status))
        raise exceptions.ErrorApi(ERROR_API.format(state=status))

    return response_json


def check_response(response):
    """Проверяется ответ API на корректность."""
    if not response:
        raise TypeError('Список пуст')
    if not isinstance(response, dict):
        raise TypeError('Некорректный ответ на запрос словаря')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('Некорректный ответ на запрос списка')
    return response['homeworks']


def parse_status(homework):
    """Извлекается из конкретной домашней работы статус этой работы."""
    status = homework['status']
    if not isinstance(HOMEWORK_STATUSES, dict):
        raise KeyError('Некорректный ответ на запрос словаря')
    message = STATUS.format(
        name=homework['homework_name'],
        verdict=HOMEWORK_STATUSES[status]
    )
    logging.info(message)
    return message


def send_message(bot, message):
    """Отправляется сообщение в Telegram чат."""
    return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def check_tokens():
    """Проверяется доступность переменных окружения."""
    tokens_fail = ''
    for name in TOKENS:
        if globals()[name] is None:
            tokens_fail += f'{name}, '
    if tokens_fail != '':
        logging.critical(TOKENS_ERROR.format(token=tokens_fail))
        return False
    return True


def main():
    """Основная логика работы бота."""
    logging.info(BOT_WORKING)
    if not check_tokens():
        raise ValueError(FAULT_TOKENS)
    current_timestamp = int(time.time())  # 1639661979 - 86400
    bot = Bot(token=TELEGRAM_TOKEN)

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = (check_response(response))
            print(homeworks)
            print(response['current_date'])
            if len(homeworks) > 0:
                status = (parse_status(homeworks[0]))
            if 'current_date' in response:
                timestamp = response.get('current_date', current_timestamp)
                send_message(bot, status)
            current_timestamp = timestamp

        except Exception as error:
            message = MESSAGE.format(faults=error)
        try:
            send_message(bot, message)
            logging.error(message)
        except Exception as error:
            logging.error(ERROR.format(fault=error))
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    record = os.path.join(PATH, 'record.log')
    logging.basicConfig(
        handlers=[logging.FileHandler(record, encoding='UTF-8',),
                  logging.StreamHandler(), ],
        level=logging.DEBUG,
        format=('%(asctime)s; %(levelname)s; %(funcName)s; '
                '№:%(lineno)s; %(message)s')
    )
    main()
