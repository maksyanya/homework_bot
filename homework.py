import logging
import os
import time

from dotenv import load_dotenv
from telegram import Bot
import requests

from exceptions import ErrorApi
from exceptions import ResponseJsonError


STATUS = 'Изменился статус проверки работы "{name}". {verdict}'
TOKENS_ERROR = 'Отсутствующие токены {token}'
PATH = os.path.abspath(__file__)
TOKENS = ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID')
BOT_WORKING = 'Бот работает'
FAULT_TOKENS = "Ошибка токенов"
MESSAGE = 'Сбой в работе программы: {faults}'
ERROR_NETWORK = 'Соединение прервано c {url}.{headers}.{params}'
RESPONSE_ERROR = ('Код ошибки:{error}. Код статуса:{state}.'
                  '{url}.{headers}.{params}')
ERROR_API = ('Ошибка при запросе к API Yandex. Код-возврата:{state}'
             '{url}.{headers}.{params}')
EMPTY_LIST = 'Список пуст'
INCORRECT_DICT = 'Некорректный ответ на запрос словаря'
INCORRECT_LIST = 'Некорректный ответ на запрос списка'
ERROR_STATUS = ('Работа остановлена из-за '
                'неожиданного принятого значения {value}')

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

VERDICTS = ('approved', 'reviewing', 'rejected')


def get_api_answer(current_timestamp):
    """Делается запрос к эндпоинту API-сервиса."""
    params = {'from_date': current_timestamp}
    parameters = dict(url=ENDPOINT, headers=HEADERS, params=params)
    try:
        homework_statuses = requests.get(**parameters)
    except requests.exceptions.ConnectionError:
        raise ConnectionError(ERROR_NETWORK.format(**parameters))
    response_json = homework_statuses.json()
    status = homework_statuses.status_code
    if status != 200:
        raise ErrorApi(ERROR_API.format(state=status, **parameters))
    for error in ['code', 'error']:
        if error in response_json:
            raise ResponseJsonError(RESPONSE_ERROR.format(
                error=response_json[error],
                state=status,
                **parameters))
    return response_json


def check_response(response):
    """Проверяется ответ API на корректность."""
    if not response:
        raise TypeError(EMPTY_LIST)
    if not isinstance(response, dict):
        raise TypeError(INCORRECT_DICT)
    if not isinstance(response.get('homeworks'), list):
        raise TypeError(INCORRECT_LIST)
    return response['homeworks']


def parse_status(homework):
    """Извлекается из конкретной домашней работы статус этой работы."""
    status = homework['status']
    if status not in VERDICTS:
        raise ValueError(ERROR_STATUS.format(value=status))
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
    timestamp = int(time.time())  # 1639661979 - 86400
    bot = Bot(token=TELEGRAM_TOKEN)

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = (check_response(response))
            if len(homeworks) > 0:
                send_message(bot, (parse_status(homeworks[0])))
            timestamp = response.get('current_date', timestamp)
        except Exception as error:
            message = MESSAGE.format(faults=error)
            try:
                send_message(bot, message)
                logging.error(message)
            except Exception as error:
                logging.error(ERROR_NETWORK.format(fault=error))
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
