# Телеграм-бот
Телеграм-бот отслеживания статуса проверки домашней работы.
## Описание
Бот работающий с API Яндекс.Практикум. Отображает статсу проверки кода ревью после отправки проектной работы. Каждые 10 минут бот проверяет API Яндекс.Практикум, и присылает в телеграм статус работы. Если работа проверена, то прийдёт сообщение в телеграме о статусе ревью проектной работы.
## Установка
1. Клонируем репозиторий: git clone https://github.com/maksyanya/homework_bot.git
2. Переходим в папку с проектом: cd homework_bot/
3. Устанавливаем виртуальное окружение для проекта: python -m venv venv
4. Активируем виртуальное окружение: venv\Scripts\activate
5. Устанавливаем необходимые зависимости для работы проекта: pip install -r requirements.txt
6. Записать в переменные окружения (файл .env) необходимые ключи:
* токен профиля на Яндекс.Практикуме
* токен телеграм-бота
* свой ID в телеграме
7. Выполнить миграции: python3 manage.py migrate
## Требования
* Python 3.7 +
* Операционная система: Linux, Windows, macOS, BSD
