import flask    # Flask is a lightweight web framework
import logging  # If errors happen, better print it to console

from google.appengine.api import users  # App Engine user authentication
from google.appengine.ext import ndb    # App Engine database

app = flask.Flask(__name__)  # Create a flask app, this var is mentioned in app.yaml


# Data model for page visit counter
# |ndb| here is the name of module imported from |google.appengine.api|
class PageVisit(ndb.Model):
    timestamp = ndb.DateTimeProperty(auto_now_add=True)  # Add current time automatically


# Data model for an item in shopping list
class ShopItem(ndb.Model):
    timestamp = ndb.DateTimeProperty(auto_now_add=True)  # Add current time automatically
    user_email = ndb.StringProperty()  # Each user has a Google account, so identified by e-mail
    text = ndb.StringProperty()  # Text itself


# Helper function to identify current user
# If |is_required| is true, exception to be raised if user has not authenticated
# Returns tuple with email and login/logout URL
def get_user_auth(is_required):
    # Get user object from App Engine API
    user = users.get_current_user()
    # |user| is None if not authenticated
    if user is None:
        if is_required:  # Not authenticated, but required to be; raise an exception
            raise ValueError('Authentication required')  # Code doesn't continue after exception
        login_url = users.create_login_url('/')  # Create URL to sign in with Google account
        return None, login_url  # Email is undefined
    else:
        # User nas authenticated
        email = user.email()
        logout_url = users.create_logout_url('/')  # Create URL to revoke authentication (logout)
        return email, logout_url


# Main page request handler, methed 'GET' is assumed by default
# Responds with rendered HTML template
@app.route('/')  # This decorator tells flask to route requests to root URL here
def main():
    # Visit counter
    visit_counter = PageVisit.query().count() + 1  # Query all entities of PageVisit and count them
    visit_record = PageVisit()  # Create a new page visit record
    visit_record.put()  # Save this record to database

    # Get current user, however it's not mandatory for main page
    auth = get_user_auth(is_required=False)
    if auth[0] is None:
        # First-time visit, so ask user to login with Google account
        return flask.render_template(  # Render template with parameters and return as response
            'main.html',  # Template file in |templates| directory
            logged_in=False,  # User hasn't authenticated
            login_url=auth[1],  # Pass login URL to the template
            visit_counter=visit_counter  # Display visit counter on the main page
        )
    else:
        # User is authenticated, so full shopping list experience is enabled
        return flask.render_template(  # Ditto, render a template
            'main.html',
            logged_in=True,
            user_email=auth[0],
            logout_url=auth[1],
            visit_counter=visit_counter
        )


# Request handler to get items from Java Script code
# Responds with list of dictionaries with id and text of each particular item
@app.route('/get_items')
def get_items():
    # Authentication is required to get a shopping list
    auth = get_user_auth(is_required=True)
    # Query entities of ShopItem which have the same |user_email| field as current user
    # Order the results by timestamp
    ndb_items = ShopItem.query(ShopItem.user_email == auth[0]).order(ShopItem.timestamp).fetch(1000)
    # App Engine database (aka ndb) has sophisticated format of result, so we need to
    # convert it to JSON-serialisable format
    json_items = []  # Start from empty list
    for ndb_item in ndb_items:  # Iterate over |ndb_items|
        # {...} creates a dictionary, so we do so and append to the list
        json_items.append({'id': ndb_item.key.integer_id(), 'text': ndb_item.text})
    return flask.jsonify(json_items)  # Serialise to JSON and return response


# Request handler to create a new item
# Responds with ID of newly created item
@app.route('/create_item', methods=['POST'])
def create_item():
    auth = get_user_auth(is_required=True)
    text = flask.request.form['text']  # Get |text| parameter from request
    key = ShopItem(user_email=auth[0], text=text).put()  # Create ShopItem entity and save it to database
    return flask.jsonify({'id': key.integer_id()})  # Return id of item's key in JSON format


# Request handler to delete an item
# Responds no data
@app.route('/delete_item', methods=['POST'])
def delete_item():
    auth = get_user_auth(is_required=True)  # Authentication is required to prevent security violation
    integer_id = int(flask.request.form['id'])  # Request should contain |id| parameter
    key = ndb.Key(ShopItem, integer_id)  # Create a key, which will identify an item
    if key.get().user_email != auth[0]:  # Entity grabbed by the key must have the same email as current user
        raise ValueError('Security violation')  # Raise an exception, can't continue
    key.delete()  # Delete the corresponding entity if everything is alright
    return flask.jsonify({})  # Dummy response


# Request handler to edit an item
# Responds no data
@app.route('/edit_item', methods=['POST'])
def edit_item():
    # Ditto, see delete_item()
    # We need to ensure security
    auth = get_user_auth(is_required=True)
    integer_id = int(flask.request.form['id'])
    entity = ndb.Key(ShopItem, integer_id).get()
    if entity.user_email != auth[0]:
        raise ValueError('Security violation')
    # If passed, change entity's text
    entity.text = flask.request.form['text']
    entity.put()  # Save changes to database
    return flask.jsonify({})  # Dummy response


# Request handle to delete entire user's list
# Responds no data
@app.route('/delete_all', methods=['POST'])
def delete_all():
    auth = get_user_auth(is_required=True)
    # Query all entities matching email of current user
    # There is no need to fetch data, so keys only
    query_iterator = ShopItem.query(ShopItem.user_email == auth[0]).iter(keys_only=True)
    # We've got an iterator and can delete items in batch
    ndb.delete_multi(query_iterator)
    return flask.jsonify({})  # Dummy response


# If something goes wrong, i.e. exception, we have to respond somehow
@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace
    # It could help with debugging
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500
