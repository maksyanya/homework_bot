import logging
import os
from typing import ValuesView
import requests
import time

from dotenv import load_dotenv
from telegram import Bot

import exceptions

STATUS = 'Изменился статус проверки работы "{name}". {verdict}'
TOKENS_ERROR = 'Отсутствует токен {token}'

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

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    encoding='UTF-8',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
)


def get_api_answer(current_timestamp):
    """Делается запрос к эндпоинту API-сервиса."""
    params = {'from_date': current_timestamp}
    homework_statuses = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params=params
    )
    if not homework_statuses:
        raise ValuesView('Нет ответа от эндопоинта API-сервиса')
    elif not homework_statuses.status_code == 200:
        raise exceptions.ErrorApi(
            'Ошибка при запросе к API Yandex.'
            f'Код-возврата:{homework_statuses.status_code}')
    else:
        return homework_statuses.json()


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
    if not isinstance(homework, dict):
        raise TypeError('Некорректный ответ на запрос словаря')
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
    for name in ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID'):
        if globals()[name] is None:
            tokens_fail += f'{str(name)}, '
    if tokens_fail != '':
        logging.critical(TOKENS_ERROR.format(token=tokens_fail))
        return False
    return True


def main():
    """Основная логика работы бота."""
    logging.info('Бот работает')
    if not check_tokens():
        raise ValueError("Ошибка токенов")
    current_timestamp = int(time.time())
    bot = Bot(token=TELEGRAM_TOKEN)

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = (check_response(response))
            if len(homeworks) > 0:
                new_status = (parse_status(homeworks[0]))
            if new_status:
                send_message(bot, new_status)
            current_timestamp = response['current_date']

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logging.error(message)
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
