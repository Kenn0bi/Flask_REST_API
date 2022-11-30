import sqlite3
from random import choice
from pathlib import Path
from flask import Flask, request, g

MIN_RATING = 1
MAX_RATING = 5

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR / "test.db"
FIELDS = ['id', 'author', 'text', 'rating']

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def to_dict(values):
    if isinstance(values, list):
        res = []
        for value in values:
            res.append(dict(zip(FIELDS, value)))
        return res
    return dict(zip(FIELDS, values))


def select_quotes(params):
    sql_query = 'SELECT * FROM quotes'
    where = None
    for key in params:
        if key in FIELDS:
            if where:
                where += f' AND {key}="{params[key]}"'
            else:
                where = f' WHERE {key}="{params[key]}"'
    if where:
        sql_query += where
    cursor = get_db().cursor()
    cursor.execute(sql_query)
    return cursor.fetchall()


def check_rating(quote):
    rating = MIN_RATING
    if quote.get('rating'):
        if isinstance(quote['rating'], int) and quote['rating'] <= MAX_RATING:
            rating = quote['rating']
    return rating


@app.route("/quotes", methods=['POST'])
def create_quote():
    data = request.json
    data['rating'] = check_rating(data)
    sql_query = f"INSERT INTO quotes (author, text, rating) VALUES (?, ?, ?);"
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute(sql_query, (data['author'], data['text'], data['rating']))
    connection.commit()
    data['id'] = cursor.lastrowid
    return data, 201


@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
    # check for empty request
    data = request.json
    if len(data) == 0:
        return 'Bad request', 400

    # check for quote existing
    quotes = select_quotes({'id': quote_id})
    if len(quotes) == 0:
        return f'Quote with id={quote_id} not found', 404

    # check for rating
    if data.get('rating'):
        data['rating'] = check_rating(data)

    fields = None
    for key in data:
        if key in FIELDS:
            if fields:
                fields += f', {key}="{data[key]}"'
            else:
                fields = f'{key}="{data[key]}"'
    sql_query = f'UPDATE quotes SET {fields} WHERE id=?'
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute(sql_query, (quote_id, ))
    connection.commit()
    return data, 201


@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def del_quote(quote_id):
    sql_query = 'DELETE FROM quotes WHERE id=?'
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute(sql_query, (quote_id, ))
    connection.commit()
    if cursor.rowcount > 0:
        return f"Quote with id {quote_id} is deleted.", 200
    return f"Quote with id={quote_id} not found", 404


@app.route("/quotes")
def get_quotes():
    return to_dict(select_quotes([]))


@app.route("/quotes/<int:quote_id>")
def get_quote_by_id(quote_id):
    quotes = select_quotes({'id': quote_id})
    if len(quotes) > 0:
        return to_dict(quotes[0])
    return f'Quote with id={quote_id} not found', 404


@app.route("/quotes/count")
def get_quotes_count():
    quotes = get_quotes()
    return {"quotes": len(quotes)}


@app.route("/quotes/random")
def get_random_quote():
    quotes = get_quotes()
    return choice(quotes)


@app.route("/quotes/filter")
def search_quotes():
    args = request.args
    return to_dict(select_quotes(args))


if __name__ == "__main__":
    app.run(debug=True)
