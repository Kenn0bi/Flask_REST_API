# Описание проекта

Учебный проект по REST API

# Инструкиция по запуску проекта
1. python3 -m venv <venv_name> - создание venv
2. source venv_name/bin/activate - активация venv
3. pip install -r requirements.txt - установка модулей
4. flask db upgrade - применение миграции
5. python app.py - запуск сервера

# Работа с API

http://127.0.0.1:5000/authors
http://127.0.0.1:5000/authors/1
http://127.0.0.1:5000/authors/1/quotes
http://127.0.0.1:5000/authors/count
http://127.0.0.1:5000/quotes
http://127.0.0.1:5000/quotes/1
