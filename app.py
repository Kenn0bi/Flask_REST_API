import random
from pathlib import Path
from flask import Flask, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

MIN_RATING = 1
MAX_RATING = 5
BASE_DIR = Path(__file__).parent

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'main.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.app_context().push()

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class QuoteModel(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   author = db.Column(db.String(32), unique=False)
   text = db.Column(db.String(255), unique=False)
   rate = db.Column(db.Integer)

   def __init__(self, author, text, rate=1):
       self.author = author
       self.text  = text
       self.rate = rate

   def __repr__(self):
       return f'Quote {self.author=}, {self.text=}, {self.rate}'

   def to_dict(self):
       return {
           "id": self.id,
           "author": self.author,
           "text": self.text,
           "rate": self.rate
       }


def check_rating(quote):
    rating = MIN_RATING
    if quote.get('rate'):
        if isinstance(quote['rate'], int) and quote['rate'] <= MAX_RATING:
            rating = quote['rate']
    return rating


@app.route("/quotes", methods=['POST'])
def create_quote():
    data = request.json
    new_quote = QuoteModel(**data)
    db.session.add(new_quote)
    db.session.commit()
    return new_quote.to_dict(), 201


@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
    data = request.json
    # check for quote existing
    quote = QuoteModel.query.get(quote_id)
    if quote is None:
        return f'Quote with id={quote_id} not found', 404

    for key in data:
        if key == 'rate':
            data[key] = check_rating(data)
        if hasattr(quote, key):
            setattr(quote, key, data[key])
    db.session.commit()

    return quote.to_dict(), 201


@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def del_quote(quote_id):
    quote = QuoteModel.query.get(quote_id)
    if quote is not None:
        db.session.delete(quote)
        db.session.commit()
        return '', 200
    return f"Quote with id={quote_id} not found", 404


@app.route("/quotes")
def get_quotes():
    quotes = QuoteModel.query.all()
    if len(quotes) > 0:
        if len(quotes) > 1:
            quotes_dict = []
            for quote in quotes:
                quotes_dict.append(quote.to_dict())
            return quotes_dict
        else:
            return quotes[0].to_dict()
    return 'Quotes not found', 404

@app.route("/quotes/<int:quote_id>")
def get_quote_by_id(quote_id):
    quote = QuoteModel.query.get(quote_id)
    if quote:
        return quote.to_dict()
    return f'Quote with id={quote_id} not found', 404


@app.route("/quotes/count")
def get_quotes_count():
    return {"quotes": QuoteModel.query.count()}


@app.route("/quotes/random")
def get_random_quote():
    quotes = get_quotes()
    return random.choice(quotes)


@app.route("/quotes/filter")
def search_quotes():
    args = request.args
    quotes = QuoteModel.query.filter_by(**args).all()
    if len(quotes) > 0:
        if len(quotes) > 1:
            quotes_dict = []
            for quote in quotes:
                quotes_dict.append(quote.to_dict())
            return quotes_dict
        else:
            return quotes[0].to_dict()
    return f'Quotes not found', 404

if __name__ == "__main__":
    app.run(debug=True)
