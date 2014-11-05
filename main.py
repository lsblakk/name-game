#!/usr/bin/env python
import sqlite3
import time, os, json
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from flask.ext.login import LoginManager, UserMixin, current_user, logout_user
from flask.ext.browserid import BrowserID
from flask.ext.sqlalchemy import SQLAlchemy
from secrets import *

# Domains allowed for log in
ALLOWED_BID = (
    'mozilla.com',
    'mozillafoundation.org',
    'mozilla-japan.org',
)

MY_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_FILES_DIR = os.path.join(MY_DIR, 'static')
JSON_FILENAME = os.path.join(MY_DIR, 'mozillians.json')
THUMBNAIL_DIR = os.path.join(STATIC_FILES_DIR, 'images', 'mozillians')
LDAP_JSON_FILENAME = os.path.join(STATIC_FILES_DIR, 'people.json')
SQLITE_DB_URI = 'sqlite:////' + os.path.join(MY_DIR, 'mozgame.db')

BASE_URL = 'https://mozillians.org/api/v1/users/'
NO_PHOTO_THUMBNAIL_SIZE = 3302

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = SQLITE_DB_URI
db = SQLAlchemy(app)

## User Model & functions for Users
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.UnicodeText, unique=True)

    def __init__(self, email):
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.email

### Login Functions ###
def get_user_by_id(id):
    """
    Given a unicode ID, returns the user that matches it.
    """
    return User.query.get(id)

def create_browserid_user(kwargs):
    """
    Takes browserid response and creates a user.
    """
    if kwargs['status'] == 'okay':
    	if kwargs['email'].split('@')[1] in ALLOWED_BID:
        	user = User(kwargs['email'])
        	db.session.add(user)
        	db.session.commit()
        	print "create_browserid_user - " + str(type(user)) + " - " + str(user)
        	return user
    else:
        return None

def get_user(kwargs):
    """
    Given the response from BrowserID, finds or creates a user.
    If a user can neither be found nor created, returns None.
    """
    u = User.query.filter(db.or_(
        User.id == kwargs.get('id'),
        User.email == kwargs.get('email')
    )).first()
    if u is None: # user didn't exist in db
        return create_browserid_user(kwargs)
    return u

app.config.from_object(__name__)

app.config['BROWSERID_LOGIN_URL'] = "/login"
app.config['BROWSERID_LOGOUT_URL'] = "/logout"
app.config['SECRET_KEY'] = SECRET_KEY
app.config['TESTING'] = True

login_manager = LoginManager()
login_manager.user_loader(get_user_by_id)
login_manager.init_app(app)

browser_id = BrowserID()
browser_id.user_loader(get_user)
browser_id.init_app(app)

## VIEWS

@app.route('/')
@app.route('/index')
def index():
	if current_user.is_authenticated():
		return render_template('name_game.html', title="Mozillians Name Game!")
	else:
		return render_template('index.html', title="Mozillians Name Game!")

@app.route('/logout')
def logout():
	logout_user()
	return redirect('/')

### Admin Tools ###
@app.route('/show_db')
def show_db():
	if current_user.is_authenticated():
		users = []
		for user in db.session.query(User):
			users.append(dict(id=user.id, email=user.email))
		return render_template('show_db.html', users=users)
	else:
		return redirect('/')

if __name__ == '__main__':
	DEBUG = os.environ.get('DEBUG', False) in ('true', '1', 'on')

	app.debug = DEBUG
	port = int(os.environ.get('PORT', 5000))
	host = os.environ.get('HOST', '0.0.0.0')
	app.run(host=host, port=port)
