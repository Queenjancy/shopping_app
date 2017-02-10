import flask
import logging

from google.appengine.api import users
from google.appengine.ext import ndb

app = flask.Flask(__name__)


class PageVisit(ndb.Model):
    timestamp = ndb.DateTimeProperty(auto_now_add=True)


class ShopItem(ndb.Model):
    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    user_email = ndb.StringProperty()
    text = ndb.StringProperty()


def get_user_auth(is_required):
    user = users.get_current_user()
    if user is None:
        if is_required:
            raise ValueError('Authentication required')
        login_url = users.create_login_url('/')
        return None, login_url
    else:
        email = user.email()
        logout_url = users.create_logout_url('/')
        return email, logout_url


@app.route('/')
def main():
    visit_counter = PageVisit.query().count() + 1
    visit_record = PageVisit()
    visit_record.put()

    auth = get_user_auth(is_required=False)
    if auth[0] is None:
        return flask.render_template(
            'main.html',
            logged_in=False,
            login_url=auth[1],
            visit_counter=visit_counter
        )
    else:
        return flask.render_template(
            'main.html',
            logged_in=True,
            user_email=auth[0],
            logout_url=auth[1],
            visit_counter=visit_counter
        )


@app.route('/get_items')
def get_items():
    auth = get_user_auth(is_required=True)
    ndb_items = ShopItem.query(ShopItem.user_email == auth[0]).order(ShopItem.timestamp).fetch(1000)
    json_items = []
    for ndb_item in ndb_items:
        json_items.append({'id': ndb_item.key.integer_id(), 'text': ndb_item.text})
    return flask.jsonify(json_items)


@app.route('/create_item', methods=['POST'])
def create_item():
    auth = get_user_auth(is_required=True)
    text = flask.request.form['text']
    key = ShopItem(user_email=auth[0], text=text).put()
    return flask.jsonify({'id': key.integer_id()})


@app.route('/delete_item', methods=['POST'])
def delete_item():
    auth = get_user_auth(is_required=True)
    integer_id = int(flask.request.form['id'])
    key = ndb.Key(ShopItem, integer_id)
    if key.get().user_email != auth[0]:
        raise ValueError('Security violation')
    key.delete()
    return flask.jsonify({})


@app.route('/delete_all', methods=['POST'])
def delete_all():
    auth = get_user_auth(is_required=True)
    query_iterator = ShopItem.query(ShopItem.user_email == auth[0]).iter(keys_only=True)
    ndb.delete_multi(query_iterator)
    return flask.jsonify({})


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500
