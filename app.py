from flask import Flask
from random import choice

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

about_me = {
   "name": "Евгений",
   "surname": "Юрченко",
   "email": "eyurchenko@specialist.ru"
}

quotes = [
   {
       "id": 3,
       "author": "Rick Cook",
       "text": "Программирование сегодня — это гонка разработчиков программ, стремящихся писать программы с большей и лучшей идиотоустойчивостью, и вселенной, которая пытается создать больше отборных идиотов. Пока вселенная побеждает."
   },
   {
       "id": 5,
       "author": "Waldi Ravens",
       "text": "Программирование на С похоже на быстрые танцы на только что отполированном полу людей с острыми бритвами в руках."
   },
   {
       "id": 6,
       "author": "Mosher’s Law of Software Engineering",
       "text": "Не волнуйтесь, если что-то не работает. Если бы всё работало, вас бы уволили."
   },
   {
       "id": 8,
       "author": "Yoggi Berra",
       "text": "В теории, теория и практика неразделимы. На практике это не так."
   },

]

@app.route("/about")
def about():
   return about_me

@app.route("/")
def hello_world():
   return "Hello, World!"

@app.route("/quotes")
def get_quotes():
   return quotes

@app.route("/quote/<int:quote_id>")
def get_quote_by_id(quote_id):
   for quote in quotes:
      if ( quote["id"] == quote_id ):
         return quote
   return f"Quote with id={quote_id} not found", 404

@app.route("/quotes/count")
def get_quotes_count():
   return { "quotes": len(quotes) }

@app.route("/somequote")
def get_some_quote():
   return choice(quotes)


if __name__ == "__main__":
   app.run(debug=True)

