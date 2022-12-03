from pathlib import Path
from sqlite3 import IntegrityError

from flask import Flask, request, g, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import validates
from sqlalchemy.exc import IntegrityError

BASE_DIR = Path(__file__).parent

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'main.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.app_context().push()

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class AuthorModel(db.Model):
    description = 'Author'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    surname = db.Column(db.String(64), unique=True)
    quotes = db.relationship('QuoteModel', backref='author', lazy='dynamic', cascade="all, delete-orphan")

    def to_dict(self):
        keys = self.__table__.columns.keys()
        values = [getattr(self, key) for key in keys]
        return dict(zip(keys, values))


class QuoteModel(db.Model):
    description = 'Quote'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey(AuthorModel.id))
    text = db.Column(db.String(255), unique=False)
    rate = db.Column(db.Integer)

    def __init__(self, author, text, rate=1):
        self.author_id = author.id
        self.text = text
        self.rate = rate

    def to_dict(self):
        keys = self.__table__.columns.keys()
        values = [getattr(self, key) for key in keys]
        res = dict(zip(keys, values))
        del res['author_id']
        res['author'] = self.author.to_dict()
        return res

    @validates("rate")
    def validate_rate(self, key, rate):
        if 0 < rate < 6:
            return rate
        abort(404, description=f"Rate must be in [1, 5]")

@app.errorhandler(404)
def not_found(e):
    response = {'status': 404, 'error': e.description}
    return response, 404

@app.errorhandler(400)
def not_found(e):
    response = {'status': 400, 'error': e.description}
    return response, 400

def get_object_or_404(model, object_id):
    object = model.query.get(object_id)
    if object is None:
        abort(404, description=f'{model.description} with id={object_id} not found')
    return object

def set_object_attr_or_400(object, data):
    for key in data:
        if hasattr(object, key):
            setattr(object, key, data[key])
        else:
            abort(400, description=f'{object.description} has not key={key}')

# AUTHOR handlers
@app.route("/authors")
def get_author():
    authors = AuthorModel.query.all()
    authors_dict = [author.to_dict() for author in authors]
    return authors_dict, 201


@app.route("/authors/<int:author_id>")
def get_author_by_id(author_id):
    author = get_object_or_404(AuthorModel, author_id)
    return author.to_dict(), 201


@app.route("/authors", methods=["POST"])
def create_author():
    author_data = request.json
    for key in author_data:
        if not hasattr(AuthorModel, key):
            return f'Wrong key={key}', 404
    author = AuthorModel(**author_data)
    db.session.add(author)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return 'Author name and surname must be unique', 400
    return author.to_dict(), 201


@app.route("/authors/<int:author_id>", methods=["PUT"])
def edit_author(author_id):
    data = request.json
    author = get_object_or_404(AuthorModel, author_id)
    set_object_attr_or_400(author, data)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return 'Author name and surname must be unique', 400
    return author.to_dict(), 201



@app.route("/authors/<int:author_id>", methods=["DELETE"])
def delete_author(author_id):
    author = get_object_or_404(AuthorModel, author_id)
    db.session.delete(author)
    db.session.commit()
    return f'Author with id={author_id} was deleted', 200


@app.route("/authors/count")
def get_authors_count():
    return {"authors": AuthorModel.query.count()}


# QUOTES handlers
@app.route("/quotes")
def get_quotes():
    quotes = QuoteModel.query.all()
    quotes_dict = [quote.to_dict() for quote in quotes]
    return quotes_dict


@app.route("/quotes/<int:quote_id>")
def get_quote_by_id(quote_id):
    quote = get_object_or_404(QuoteModel, quote_id)
    return quote.to_dict()


@app.route("/authors/<int:author_id>/quotes")
def author_quotes(author_id):
    author = get_object_or_404(AuthorModel, author_id)
    quotes = author.quotes.all()
    quotes_dict = [quote.to_dict() for quote in quotes]
    return quotes_dict, 200


@app.route("/authors/<int:author_id>/quotes", methods=["POST"])
def create_quote(author_id):
    author = get_object_or_404(AuthorModel, author_id)
    new_quote = request.json
    q = QuoteModel(author, new_quote["text"])
    db.session.add(q)
    db.session.commit()
    return q.to_dict(), 201


@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
    data = request.json
    quote = get_object_or_404(QuoteModel, quote_id)
    set_object_attr_or_400(quote, data)
    db.session.commit()
    return quote.to_dict(), 201


@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def del_quote(quote_id):
    quote = get_object_or_404(QuoteModel, quote_id)
    db.session.delete(quote)
    db.session.commit()
    return '', 200


@app.route("/quotes/count")
def get_quotes_count():
    return {"quotes": QuoteModel.query.count()}


@app.route("/quotes/random")
def get_random_quote():
    quote = QuoteModel.query.order_by(func.random()).first()
    if quote:
        return quote.to_dict(), 200
    return 'Quotes not found', 404


@app.route("/quotes/filter")
def search_quotes():
    args = request.args
    for key in args:
        if key in QuoteModel.__table__.columns.keys():
            if key == 'author_id':
                author = get_object_or_404(AuthorModel, args[key])
        else:
            abort(400, description=f'{QuoteModel.description} has not key={key}')
    quotes = QuoteModel.query.filter_by(**args).all()
    if quotes:
        quotes_dict = [quote.to_dict() for quote in quotes]
        return quotes_dict
    return f'Quotes not found', 404

@app.route("/quotes/<int:quote_id>/rate/up")
def up_quote_rate(quote_id):
    quote = get_object_or_404(QuoteModel, quote_id)
    setattr(quote, 'rate', getattr(quote, 'rate')+1)
    db.session.commit()
    return quote.to_dict(), 201


@app.route("/quotes/<int:quote_id>/rate/down")
def down_quote_rate(quote_id):
    quote = get_object_or_404(QuoteModel, quote_id)
    setattr(quote, 'rate', getattr(quote, 'rate')-1)
    db.session.commit()
    return quote.to_dict(), 201


if __name__ == "__main__":
    app.run(debug=True)
