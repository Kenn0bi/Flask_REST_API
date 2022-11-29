from flask import Flask
from random import choice
from flask import request

MIN_RATING = 1
MAX_RATING = 5

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
       "text": "Программирование сегодня — это гонка разработчиков программ, стремящихся писать программы с большей и лучшей идиотоустойчивостью, и вселенной, которая пытается создать больше отборных идиотов. Пока вселенная побеждает.",
       "rating": 2
   },
   {
       "id": 5,
       "author": "Waldi Ravens",
       "text": "Программирование на С похоже на быстрые танцы на только что отполированном полу людей с острыми бритвами в руках.",
       "rating": 2
   },
   {
       "id": 6,
       "author": "Mosher’s Law of Software Engineering",
       "text": "Не волнуйтесь, если что-то не работает. Если бы всё работало, вас бы уволили.",
       "rating": 2
   },
   {
       "id": 8,
       "author": "Yoggi Berra",
       "text": "В теории, теория и практика неразделимы. На практике это не так.",
       "rating": 2
   },

]

def find_quote(quote_id):
    for quote in quotes:
        if (quote['id'] == quote_id):
            return quote


def check_rating(quote):
    rating = MIN_RATING
    if quote.get('rating'):
        if isinstance(quote['rating'], int) and quote['rating'] <= MAX_RATING:
            rating = quote['rating']
    return rating


@app.route("/quotes", methods=['POST'])
def create_quote():
   data = request.json
   new_quote = data
   new_quote['rating'] = check_rating(new_quote)
   new_quote['id'] = quotes[-1]['id'] + 1
   quotes.append(new_quote)
   print("data = ", data)
   return new_quote, 201


@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
    new_data = request.json
    quote = find_quote(quote_id)
    if quote:
        new_data['rating'] = check_rating(new_data)
        for key in new_data:
            quote[key] = new_data[key]
        return '', 200
    return f"Quote with id={quote_id} not found", 404


@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def del_quote(quote_id):
    quote = find_quote(quote_id)
    if quote:
        quotes.remove(quote)
        return f"Quote with id {quote_id} is deleted.", 200
    return f"Quote with id={quote_id} not found", 404


@app.route("/about")
def about():
   return about_me


@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route("/quotes")
def get_quotes():
    return quotes


@app.route("/quotes/<int:quote_id>")
def get_quote_by_id(quote_id):
    quote = find_quote(quote_id)
    if quote:
        return quote
    return f"Quote with id={quote_id} not found", 404


@app.route("/quotes/count")
def get_quotes_count():
   return { "quotes": len(quotes) }


@app.route("/quotes/random")
def get_random_quote():
   return choice(quotes)


@app.route("/quotes/filter")
def search_quotes():
    def check_quote(quote, args):
        # check for keys validation
        for key in args:
            if not quote.get(key):
                return False
        # search for values
        for key in args:
            value = int(args[key]) if key in ('rating', 'id') else args[key]
            if quote[key] != value:
                return False
        return True

    args = request.args
    return list(filter(lambda x: check_quote(x, args), quotes))


if __name__ == "__main__":
    app.run(debug=True)


