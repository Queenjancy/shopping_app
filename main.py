import flask
import logging

from google.appengine.api import users
from google.appengine.ext import ndb

app = flask.Flask(__name__)


class PageVisit(ndb.Model):
    timestamp = ndb.DateTimeProperty(auto_now_add=True)


@app.route('/')
def main():
    return flask.render_template('main.html')


@app.route('/get_items')
def get_items():
    items = [
        {'id': 1, 'text': 'Eggs'},
        {'id': 2, 'text': 'Spinach'},
        {'id': 3, 'text': 'Milk'},
    ]
    return flask.jsonify(items)


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
