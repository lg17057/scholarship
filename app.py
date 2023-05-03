#used for sql
from select import select
import sqlite3 as sql
from sqlite3 import *
#used for hashing
import hashlib
import re
#for generating secrect key
import os
#used for data on dates
from datetime import date, timedelta
import datetime
#used for preventing sql errors
import time
from time import sleep
#general imports for flask
from flask import Flask, render_template, url_for, redirect, request, make_response, jsonify, session

app = Flask(__name__, static_url_path='/static')
#randomly generates secret key
app.secret_key = 'keykeykeykeykeykeykey'

#Notes:
#
#
#






#This class is used to open a database connection and automatically close it
#Use as such:
# with opendb('filename') as c:
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
def device_logs():
    with opendb('logs.db') as c:
        #fetches all devices and all associated data
        c.execute("SELECT * from devices")
        devices = c.fetchall()

        return render_template('/device_logs.html', rows=devices)

#
@app.route('/sign-off')
def sign_off():
    with opendb('logs.db') as c:
        #selects all data from rental logs where data is unconfirmed
        c.execute("SELECT * FROM device_logs WHERE teacher_signoff='Unconfirmed'")
        rows = c.fetchall()
        return render_template('sign_off.html', rows=rows)

#
@app.route('/modify-device')
def modify_device():
    return render_template('modify_devices.html')

@app.route('/circulations')
def circulations():
    with opendb('logs.db') as c:
        #The below section is proof of concept. The ipads,chromebooks and laptops_circulating variables will become dynamic
        ipads_circulating = 'None circulating'
        chromebooks_circulating = 'None circulating'
        laptops_circulating = 'None circulating'

        #Finding the number of each device type that is in circulation; key in_circulation Yes
        c.execute("SELECT COUNT(*) FROM devices WHERE device_type='iPad' AND in_circulation='Yes'")
        ipads_circulating = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM devices WHERE device_type='Chromebook' AND in_circulation='Yes'")
        chromebooks_circulating = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM devices WHERE device_type='Laptop' AND in_circulation='Yes'")
        laptops_circulating = c.fetchone()[0]
        c.execute('SELECT device_logs.date_borrowed, devices.device_type, device_logs.device_id, device_logs.period_borrowed, device_logs.reason_borrowed FROM device_logs INNER JOIN devices ON device_logs.device_id = devices.device_id')
        circulating_data = c.fetchall()
        return render_template('circulations.html', ipads_c=ipads_circulating, chromebooks_c=chromebooks_circulating, laptops_c=laptops_circulating, rows=circulating_data )

#Page created for displaying different device rental and creation statistics
@app.route('/statistics')
def statistics():
    return render_template('statistics.html')

#Page designed for data on students
@app.route('/students')
def students():
    return render_template('students.html')

#Displays all rental logs in a table
#
@app.route('/rental-logs')
def rental_logs():
    with opendb('logs.db') as c:
        #selects all data from device_logs, resulting in all rental data being displayed
        c.execute("SELECT * from device_logs")
        logs = c.fetchall()
        return render_template('rental_logs.html', rows=logs)

#
@app.route('/new-log')
@app.route('/new-log', methods=['POST'])
def new_log():
    with opendb('logs.db') as c:
        if request.method == "POST": #If user clicks submit button
            date_borrowed = datetime.datetime.now().strftime("%Y-%m-%d %H:%M") #Automatically logs the date and time a device was rented
            student_name = request.form.get('student_name') 
            homeroom = request.form.get('homeroom') 
            device_type = request.form.get('device_type')
            device_id = request.form.get('device_id')
            period_borrowed = request.form.get('period_borrowed')
            reason_borrowed = request.form.get('reason_borrowed')
            period_returned = request.form.get('period_returned')
            submitted_under = session['user_id']

            teacher_signoff = request.form.get('teacher_signoff')
            notes = request.form.get('notes')

           #submits log data
            c.execute("INSERT INTO device_logs (date_borrowed, submitted_under, student_name, homeroom, device_type, device_id, period_borrowed, reason_borrowed, period_returned, teacher_signoff, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (date_borrowed, submitted_under, student_name, homeroom, device_type, device_id, period_borrowed, reason_borrowed, period_returned, teacher_signoff, notes))
            return render_template('message.html', message="successful device log")
        else:
            return render_template('new_log.html')

#
@app.route('/new-item')
@app.route('/new-item', methods=['POST'])
def new_item():
    with opendb('logs.db') as c:
        if request.method == "POST": #when user clicks submit button
            #used for creating a new device
            device_id = request.form['device_id'] #may be replaced by a unique qr code instead of an id 
            device_type = request.form['device_type']
            date_submitted = datetime.datetime.now().strftime("%Y-%m-%d %H:%M") #records date and time device was created
            #^ re-evaluate the data format
            submitted_by = session['user_id']
            notes_device = request.form['notes']
            in_circulation = "No"
            c.execute("INSERT INTO devices (device_id, device_type, date_added, added_by, in_circulation, notes) VALUES (?, ?, ?, ?, ?, ?)", (device_id, device_type, date_submitted, submitted_by, in_circulation, notes_device))
            return render_template('message.html', message="new device logged")
        else:
            return render_template('new_item.html')
#
@app.route('/dev-admin')
def dev_admin():

    return render_template('/dev_admin.html')

#
@app.route('/admin')
def admin():
    return render_template('/admin.html')

@app.route('/logout', methods=["GET", "POST"])
def logout():
    if 'logged_in' in session and session['logged_in']:
        #setting login status and user id to False and invalid, respectfully
        session['logged_in'] = False
        session['user_id'] = "Invalid"
        return render_template('/message.html', message="You have been logged out")
    else:
        return render_template('/message.html', message="You are already not logged in")

#
@app.route('/login-page')
def login_page():
    return render_template('/login_page.html')

#
def login_success(teacher_name, last_login):
    with opendb('main.db') as c:
        c.execute("SELECT logins FROM users WHERE teacher_name = ?", (teacher_name,))
        c.execute("UPDATE users SET logins = logins + 1 WHERE teacher_name = ?", (teacher_name,))
        #updates number of successful logins for a teaceher
        c.execute("UPDATE users SET last_login = ?", (last_login,))
        #sets last_login value to current date and time 
#   
@app.route('/login-page', methods=["POST"])
def login_page_post():
    with opendb('main.db') as c:
        teacher_name = request.form['teacher_name'] #fetches teacher name
        passkey = request.form['password'] #fetches password
        passkey_h = hashlib.sha256(passkey.encode('utf-8')).hexdigest() #hashes password
        c.execute('SELECT * FROM users WHERE teacher_name=? AND password=?', (teacher_name, passkey_h)) #selects username and hashed pword from database
        user_validation = c.fetchone()
        if user_validation:
            session['logged_in'] = True
            session['user_id'] = teacher_name
            last_login = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

            login_success(teacher_name, last_login)

            return render_template('message.html', message="Login Success")
        else:
            session['logged_in'] = False
            session['user_id'] = "Invalid"
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
            c.execute('INSERT INTO users (teacher_name, email, password, logins, date_created, last_login) VALUES (?, ?, ?, ?, ?, ?)', (teacher_name, email, passkey_h, logins, date_created, "N/A"))
            return render_template('message.html', message="Sign Up success")
        else:
            return render_template('message.html', message='Sign Up failure.')

#
@app.route('/message')
def message():
    return render_template('message.html')

############################################# End-user oriented
# help page
@app.route('/help')
def help():
    return render_template('help.html')
#Handles 400 errors -
@app.errorhandler(400)
def bad_request_error(error):
    return render_template('error_page.html',error_code="400", error_message="Bad Request"), 400
#Handles 401 errors - 
@app.errorhandler(401)
def unauthorized_error(error):
    return render_template('error_page.html',error_code="401", error_message="Unauthorized"), 401
#Handles 403 errors -
@app.errorhandler(403)
def forbidden_error(error):
    return render_template('error_page.html',error_code="403", error_message="Forbidden"), 403
#Handles 404 errors -
@app.errorhandler(404)
def page_not_found_error(error):
    return render_template('error_page.html',error_code="404", error_message="Not Found"), 404
#Handles 405 errors -
@app.errorhandler(405)
def method_not_allowed_error(error):
    return render_template('error_page.html',error_code="405", error_message="Method Not Allowed"), 405
#Handles 500 errors -
@app.errorhandler(500)
def internal_server_error(error):
    sql.session.rollback()
    return render_template('error_page.html',error_code="500", error_message="Internal Server Error"), 500
#Handles 503 errors -
@app.errorhandler(503)
def service_unavailable_error(error):
    return render_template('error_page.html',error_code="503", error_message="Service Unavailable"), 503




# Responsible for running the website
if __name__ == '__main__':
    app.run(debug="True")

