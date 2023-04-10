# python -m flask run
from select import select
import sqlite3 as sql
from sqlite3 import *
import hashlib
import re
from datetime import date
import datetime
import time
from time import sleep
from flask import Flask, render_template, url_for, redirect, request, make_response
app = Flask(__name__, static_url_path='/static')

class opendb():
    def __init__(self, file_name):
        self.obj = sql.connect(file_name)
        self.cursor = self.obj.cursor()
    
    def __enter__(self):
        return self.cursor
    
    def __exit__(self, value, traceback, type):
        time.sleep(1)
        self.obj.commit()
        self.obj.close()


# Home page
@app.route('/')
def main():
    return render_template('/index.html')

#device log page
@app.route('/device-logs')
def index():
    return render_template('/device_logs.html')

#
@app.route('/dev-admin')
def dev_admin():
    
    return render_template('/dev_admin.html')

#
@app.route('/admin')
def admin():
    return render_template('/admin.html')

#
@app.route('/login-page')
def login_page():
    return render_template('/login_page.html')

#
@app.route('/login-page', methods=["POST"])
def login_page_post():
    with opendb('main.db') as c:
        teacher_name = request.form['teacher_name']
        passkey = request.form['password']
        passkey_h = hashlib.sha256(passkey.encode('utf-8')).hexdigest()
        c.execute('SELECT * FROM users WHERE teacher_name=? AND password=?', (teacher_name, passkey_h))
        user_validation = c.fetchone()
        if user_validation:
            return render_template('message.html', message="Login Success")
        else:
            return render_template('message.html', message="Login Failure")

#
@app.route('/signup-page')
def signup_page():
    return render_template('/signup_page.html')
#
@app.route('/signup-page', methods=['POST'])
def signup_page_post():
    with opendb('main.db') as c:
        teacher_name = request.form['teacher_name']
        cursor = c.execute('SELECT teacher_name FROM users WHERE teacher_name=?', (teacher_name,))
        user_check = cursor.fetchall()
        now = datetime.datetime.now()
        date_created = now.strftime("%d/%m/%Y %H:%M")
        if user_check != 0: #checks if user exists
            email = request.form['email']
            passkey = request.form['password']
            logins=0
            passkey_h = hashlib.sha256(passkey.encode('utf-8')).hexdigest()
            c.execute('INSERT INTO users (teacher_name, email, password, logins, date_created) VALUES (?, ?, ?, ?, ?)', (teacher_name, email, passkey_h, logins, date_created))
            return render_template('message.html', message="Sign Up success")
        else:
            return render_template('message.html', message='Sign Up failure.')

#
@app.route('/message')
def message():
    return render_template('message.html')

############################################# Error catching
#Handles 400 errors -
@app.errorhandler(400)
def bad_request_error(error):
    return render_template('error_page.html'), 400

#Handles 401 errors - 
@app.errorhandler(401)
def unauthorized_error(error):
    return render_template('error_page.html'), 401

#Handles 403 errors -
@app.errorhandler(403)
def forbidden_error(error):
    return render_template('error_page.html'), 403

#Handles 404 errors -
@app.errorhandler(404)
def page_not_found_error(error):
    return render_template('error_page.html'), 404

#Handles 405 errors -
@app.errorhandler(405)
def method_not_allowed_error(error):
    return render_template('error_page.html'), 405

#Handles 500 errors -
@app.errorhandler(500)
def internal_server_error(error):
    sql.session.rollback()
    return render_template('error_page.html'), 500

#Handles 503 errors -
@app.errorhandler(503)
def service_unavailable_error(error):
    return render_template('error_page.html'), 503




# Responsible for running the website
if __name__ == '__main__':
    app.run(debug="True")