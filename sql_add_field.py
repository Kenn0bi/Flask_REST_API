import sqlite3

select_quotes = "ALTER TABLE quotes ADD rating INTEGER DEFAULT 1"
# Подключение в БД
connection = sqlite3.connect("test.db")
# Создаем cursor, он позволяет делать SQL-запросы
cursor = connection.cursor()
# Выполняем запрос:
cursor.execute(select_quotes)

# Закрыть курсор:
cursor.close()