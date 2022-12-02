from random import choice
from pathlib import Path
from flask import Flask, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

BASE_DIR = Path(__file__).parent

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'main.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.app_context().push()

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class AuthorModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    surname = db.Column(db.String(64), unique=True)
    quotes = db.relationship('QuoteModel', backref='author', lazy='dynamic', cascade="all, delete-orphan")

    def to_dict(self):
        keys = self.__table__.columns.keys()
        values = [getattr(self, key) for key in keys]
        return dict(zip(keys, values))


class QuoteModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey(AuthorModel.id))
    text = db.Column(db.String(255), unique=False)

    def __init__(self, author, text):
        self.author_id = author.id
        self.text = text

    def to_dict(self):
        return {
            "id": self.id,
            "author": self.author.to_dict(),
            "text": self.text
        }


# AUTHOR handlers
@app.route("/authors")
def get_author():
    authors = AuthorModel.query.all()
    if len(authors) > 0:
        if len(authors) > 1:
            authors_dict = [author.to_dict() for author in authors]
            return authors_dict, 201
        return authors[0].to_dict(), 201
    return 'Authors not found', 404


@app.route("/authors/<int:author_id>")
def get_author_by_id(author_id):
    author = AuthorModel.query.get(author_id)
    if author:
        return author.to_dict(), 201
    return f'Author with id={author_id} not found', 404


@app.route("/authors", methods=["POST"])
def create_author():
    author_data = request.json
    for key in author_data:
        if not hasattr(AuthorModel, key):
            return f'Wrong key={key}', 404
    author = AuthorModel(**author_data)
    db.session.add(author)
    db.session.commit()
    return author.to_dict(), 201


@app.route("/authors/<int:author_id>", methods=["PUT"])
def edit_author(author_id):
    data = request.json
    author = AuthorModel.query.get(author_id)
    if author is None:
        return f'Author with id={author_id} not found', 404
    for key in data:
        if hasattr(author, key):
            setattr(author, key, data[key])
    db.session.commit()
    return author.to_dict(), 201


@app.route("/authors/<int:author_id>", methods=["DELETE"])
def delete_author(author_id):
    author = AuthorModel.query.get(author_id)
    if author:
        db.session.delete(author)
        db.session.commit()
        return f'Author with id={author_id} was deleted', 200
    return f"Author with id={author_id} not found", 404


@app.route("/authors/count")
def get_authors_count():
    return {"authors": AuthorModel.query.count()}


# QUOTES handlers
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


@app.route("/authors/<int:author_id>/quotes")
def author_quotes(author_id):
    author = AuthorModel.query.get(author_id)
    quotes = author.quotes.all()
    if len(quotes) > 0:
        if len(quotes) > 1:
            quotes_dict = []
            for quote in quotes:
                quotes_dict.append(quote.to_dict())
            return quotes_dict, 200
        return quotes[0].to_dict()
    return f'Quotes not found for author_id={author_id}'


@app.route("/authors/<int:author_id>/quotes", methods=["POST"])
def create_quote(author_id):
    author = AuthorModel.query.get(author_id)
    if author:
        new_quote = request.json
        q = QuoteModel(author, new_quote["text"])
        db.session.add(q)
        db.session.commit()
        return q.to_dict(), 201
    return f'Author with id={author_id} not found', 404


@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
    data = request.json
    quote = QuoteModel.query.get(quote_id)
    if quote is None:
        return f'Quote with id={quote_id} not found', 404
    for key in data:
        if hasattr(quote, key):
            if key == 'author_id':
                author = AuthorModel.query.get(data[key])
                if author is None:
                    return f'Author with id={data[key]} not found', 404
            setattr(quote, key, data[key])
        else:
            return f'Quote has not key={key}', 404
    db.session.commit()
    return quote.to_dict(), 201


@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def del_quote(quote_id):
    quote = QuoteModel.query.get(quote_id)
    if quote is not None:
        db.session.delete(quote)
        db.session.commit()
        return f'Quote with id={quote_id} was deleted', 200
    return f'Quote with id={quote_id} not found', 404


@app.route("/quotes/count")
def get_quotes_count():
    return {"quotes": QuoteModel.query.count()}


@app.route("/quotes/random")
def get_random_quote():
    quotes = QuoteModel.query.all()
    if len(quotes) > 0:
        if len(quotes) > 1:
            random_quote = choice(quotes)
            return random_quote.to_dict(), 200
        return quotes[0].to_dict(), 200
    return 'Quotes not found', 404


@app.route("/quotes/filter")
def search_quotes():
    args = request.args

    for key in args:
        if key in QuoteModel.__table__.columns.keys():
            if key == 'author_id':
                author = AuthorModel.query.get(args[key])
                if author is None:
                    return f'Author with id={args[key]} not found', 404
        else:
            return f'Quote has not key={key}', 404
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
