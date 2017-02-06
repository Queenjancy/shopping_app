import logging

from flask import Flask
from google.appengine.ext import ndb

app = Flask(__name__)


class PageVisit(ndb.Model):
    timestamp = ndb.DateTimeProperty(auto_now_add=True)


@app.route('/')
def hello_world():
    visited_so_far = PageVisit.query().count() + 1
    visit_record = PageVisit()
    visit_record.put()
    return 'Visited {0} times.'.format(visited_so_far)


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500
