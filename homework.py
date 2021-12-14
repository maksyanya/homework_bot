import os
from telegram import Bot
import time
import requests
from dotenv import load_dotenv
import logging
import exceptions

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
    timestamp = current_timestamp or int(time.time())
    url = ENDPOINT
    headers = HEADERS
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(url, headers=headers, params=params)
        response = homework_statuses.json()
        if not homework_statuses.status_code // 100 == 2:
            raise exceptions.ErrorApi('Ошибка при запросе к API Yandex')
        return response
    except TimeoutError as error:
        logging.error(f'Ошибка при запросе к API Yandex: {error}')


def check_response(response):
    """Проверяется ответ API на корректность."""
    if not response:
        raise exceptions.TypeError('Список пуст')
    if not isinstance(response, dict):
        raise exceptions.TypeError('Некорректный ответ на запрос словаря')
    if not isinstance(response.get('homeworks'), list):
        raise exceptions.TypeError('Некорректный ответ на запрос списка')
    return response['homeworks']


def parse_status(homework):
    """Извлекается из конкретной домашней работы статус этой работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES[homework_status]
    message = f'Изменился статус проверки работы "{homework_name}". {verdict}'
    logging.info(message)
    return message


def send_message(bot, message):
    """Отправляется сообщение в Telegram чат."""
    bot = Bot(token=TELEGRAM_TOKEN)
    return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def check_tokens():
    """Проверяется доступность переменных окружения."""
    if not PRACTICUM_TOKEN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    return True


def main():
    """Основная логика работы бота."""
    logging.info('Бот работает')
    last_status = []
    if not check_tokens():
        raise exceptions.ValueErrorTokens("Ошибка токенов")
    current_timestamp = int(time.time())
    bot = Bot(token=TELEGRAM_TOKEN)

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = (check_response(response))
            if len(homeworks[0]) > 1:
                new_status = (parse_status(homeworks[0]))
            if last_status != new_status:
                send_message(bot, new_status)
            last_status = new_status
            time.sleep(RETRY_TIME)
            current_timestamp = int(time.time())

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logging.error(message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    if check_tokens():
        main()
