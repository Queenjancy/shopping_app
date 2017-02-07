import flask
import logging

from google.appengine.api import users
from google.appengine.ext import ndb

app = flask.Flask(__name__)


class PageVisit(ndb.Model):
    timestamp = ndb.DateTimeProperty(auto_now_add=True)


class ShopItem(ndb.Model):
    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    text = ndb.StringProperty()


@app.route('/')
def main():
    return flask.render_template('main.html')


@app.route('/get_items')
def get_items():
    ndb_items = ShopItem.query().order(ShopItem.timestamp).fetch(1000)
    json_items = []
    for ndb_item in ndb_items:
        json_items.append({'id': ndb_item.key.integer_id(), 'text': ndb_item.text})
    return flask.jsonify(json_items)


@app.route('/create_item', methods=['POST'])
def create_item():
    text = flask.request.form['text']
    key = ShopItem(text=text).put()
    return flask.jsonify({'id': key.integer_id()})


@app.route('/delete_item', methods=['POST'])
def delete_item():
    integer_id = int(flask.request.form['id'])
    key = ndb.Key(ShopItem, integer_id)
    key.delete()
    return flask.jsonify({})


@app.route('/hello')
def hello_world():
    # User authentication.
    user = users.get_current_user()
    if user is not None:
        email = user.email()
        logout_url = users.create_logout_url('/')
        greeting = 'Welcome, {0}! (<a href="{1}">Sign out</a>)'.format(email, logout_url)
    else:
        login_url = users.create_login_url('/')
        greeting = '<a href="{0}">Sign in</a>'.format(login_url)

    # Visit counter.
    visited_so_far = PageVisit.query().count() + 1
    visit_record = PageVisit()
    visit_record.put()

    return """
        <html>
        <body>
        <p>{0}</p>
        <p>Visited {1} times.</p>
        </body>
        </html>
        """.format(greeting, visited_so_far)


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500
