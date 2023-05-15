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
from flask import Flask, render_template, url_for, redirect, request, make_response, jsonify, session, Response, send_file
from barcode import EAN13
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io
#used for multiple purposes
from io import BytesIO
#used for generating barcode
import barcode
import binascii
from barcode.writer import ImageWriter
import csv

#defines static file path
app = Flask(__name__, static_url_path='/static')   
#randomly generates secret key for sessions
app.secret_key = 'ajnasdN&aslpo0912nlasiqwenz'

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

#used as a way to determine whether or not a user is logged in before accessing the website's features
class login_verification():
    def __enter__(self):
        loginstatus = session['logged_in']
        if loginstatus is True:
            return 
        elif loginstatus is False:
            return render_template('message.html', message="Please login to access this feature", message_btn="Login",message_link="login-page")
        else: 
            return render_template('message.html', message="An error occurred. Please try again", message_btn="Login",message_link="login-page")

    def __exit__(self, type, value, traceback):
        return

# Home page
@app.route('/')
def main():
    return render_template('/index.html')

#device log page

@app.route('/device-logs')
def device_logs():
    with opendb('logs.db') as c:
        #selects all device logs data
        c.execute('SELECT * FROM devices')

        rows = c.fetchall()
        loginstatus = session['logged_in']
        return render_template('/device_logs.html', rows=rows, loginstatus=loginstatus, device_id=rows)

#used to provide link for the device barcode;

#format example; /barcode/Chromebook/2231

@app.route('/barcode/<string:device_type>/<int:device_id>')
def get_barcode(device_type, device_id):
    with opendb('logs.db') as c:
        c.execute('SELECT barcode FROM devices WHERE device_id = ? and device_type = ?', (device_id,device_type,))
        barcode_data = c.fetchone()[0]
        return Response(barcode_data, mimetype='image/png')

#Page dedicated for the ability to modify devices and relevant data
@app.route('/modify-device')
def modify_device():
    return render_template('modify_devices.html')


#page used to view current circulating devices that have NOT been returned
@app.route('/circulations')
def circulations():
    with opendb('logs.db') as c:
        # The below section is proof of concept. The ipads, chromebooks, and laptops_circulating variables will become dynamic
        ipads_circulating = 'None circulating'
        chromebooks_circulating = 'None circulating'
        laptops_circulating = 'None circulating'

        # Finding the number of each device type that is in circulation; key in_circulation Yes
        c.execute("SELECT COUNT(*) FROM devices WHERE device_type='iPad' AND in_circulation='Yes'")
        ipads_circulating = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM devices WHERE device_type='Chromebook' AND in_circulation='Yes'")
        chromebooks_circulating = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM devices WHERE device_type='Laptop' AND in_circulation='Yes'")
        laptops_circulating = c.fetchone()[0]

        # Selecting only devices that are currently in circulation
        c.execute('SELECT device_logs.date_borrowed, devices.device_type, device_logs.device_id, device_logs.period_borrowed, device_logs.reason_borrowed '
                  'FROM device_logs INNER JOIN devices ON device_logs.device_id = devices.device_id '
                  'WHERE devices.in_circulation = "Yes"')
        circulating_data = c.fetchall()

        return render_template('circulations.html', ipads_c=ipads_circulating, chromebooks_c=chromebooks_circulating,
                               laptops_c=laptops_circulating, rows=circulating_data)


#Page created for displaying different device rental and creation statistics
@app.route('/general-data')
def general_data():
    return render_template('statistics.html')


#Page designed for data on students
@app.route('/student-data')
def student_data():
    loginstatus = session['logged_in']
    return render_template('students.html', loginstatus=loginstatus)

#page for homeroom data
@app.route('/homeroom-data')
def homeroom_data():
    loginstatus = session['logged_in']
    return render_template('homeroom_data.html', loginstatus=loginstatus)

#Displays all rental logs in a table 
#user can select what data of rental logs to see;

#example of date specific viewing; /rental-logs/11-04 


@app.route('/rental-logs/<string:date>')
def rental_logs_date(date):
    with opendb('logs.db') as c:
        c.execute("SELECT * FROM device_logs WHERE date_borrowed LIKE ?", (f"%{date}%",))
        rows = c.fetchall()
        loginstatus = session['logged_in']
        return render_template('rental_logs.html', rows=rows, message="Viewing rental logs for {}".format(date), loginstatus=loginstatus)
 
@app.route('/rental-logs/', methods=['GET', 'POST'])
def rental_logs():
    with opendb('logs.db') as c:
        today = date.today()
        formatted_date = today.strftime("%Y-%H-%m")
        c.execute("SELECT * from device_logs")
        logs = c.fetchall()
        loginstatus = session['logged_in']
        if request.method == 'POST':
            device_type = request.form.get('devicepicker')
            device_id = request.form.get('idpicker')
            return redirect('/rental-logs/{}/{}'.format(device_type, device_id))
        return render_template('rental_logs.html', rows=logs, message="Viewing all rental logs", formatted_date=formatted_date, loginstatus=loginstatus)
#page for user to view device specific rental logs 
#example of route;  /rental-logs/2231

@app.route('/rental-logs/<string:device_type>/<int:device_id>')
def date_id_logs(device_type, device_id):
    with opendb('logs.db') as c:
        c.execute("SELECT * from device_logs WHERE device_type = ? AND device_id = ?", (device_type, device_id,))
        rows = c.fetchall()
        loginstatus = session.get('logged_in', False)
        message = "Viewing rental logs for {} ID {}".format(device_type, device_id)
        return render_template('rental_logs.html', loginstatus=loginstatus, rows=rows, message=message)

@app.route('/download-logs/')
def download_logs():
    with opendb('logs.db') as c:
        blah = 'blah'
        loginstatus = session['logged_in']
        return render_template('/download_logs.html', loginstatus=loginstatus, message="Download All Rental Data" )


#page used to sign off circulations that have been returned
@app.route('/sign-off')
def sign_off():
    with opendb('logs.db') as c:
        #selects all data from rental logs where data is unconfirmed
        c.execute("SELECT device_id, date_borrowed, submitted_under, student_name, homeroom, period_borrowed, reason_borrowed, period_returned, notes FROM device_logs WHERE teacher_signoff='Unconfirmed' AND period_returned IN (1, 2, 3, 4, 5, 6) AND period_returned != 'Not Returned'")
        rows = c.fetchall()
        loginstatus = session['logged_in']

        return render_template('sign_off.html', rows=rows, loginstatus=loginstatus, message="Viewing unconfirmed circulations")

#Used to sign off a device based off of id; 
#can be used to rectify an issue where a device is trying to be rented and has not been confirmed as returned
@app.route('/sign-off/<string:device_type>/<int:device_id>')
def sign_off_deviceid(device_type,device_id):
    with opendb('logs.db') as c:
            c.execute('SELECT * FROM device_logs WHERE device_type = ? AND device_id = ? AND teacher_signoff = "Unconfirmed" AND period_returned NOT IN ("Not Returned")', (device_type, device_id,))

            rows = c.fetchall()
        
            loginstatus = session['logged_in']
            return render_template('/device_modifier.html', loginstatus=loginstatus, rows=rows, message="Sign Off Device ID {}".format(device_id))

#Link that confirms entries after devices have been selected to sign off
@app.route('/confirm-entries', methods=['POST'])
def confirm_entries():
    with sql.connect('logs.db') as c:
        device_ids = request.form.getlist('device_ids[]')
        loginstatus = session['logged_in']
        if device_ids:
            try:
                c.execute('UPDATE device_logs SET teacher_signoff = "Confirmed" WHERE device_id IN ({})'.format(','.join('?' * len(device_ids))), device_ids)
                message = 'Selected entries have been confirmed.'
                message_type = 'success'
                c.commit()
            except sql.Error as e:
                print('Error confirming entries:', e)
                c.rollback()
                message = 'An error occurred while confirming entries.'
                message_type = 'error'
            finally:
                c.close()
        else:
            message = 'No entries selected for confirmation.'
            message_type = 'info'

        return render_template('message.html', message=message, loginstatus=loginstatus, message_btn="View_Circulations",message_link="circulations")




@app.route('/new-log')
@app.route('/new-log', methods=['POST'])
def new_log():
    with opendb('logs.db') as c:
        loginstatus = session['logged_in']

        if loginstatus:
            if request.method == "POST":
                # Retrieve form data
                date_borrowed = datetime.datetime.now().strftime("%d-%m %H:%M")
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

                # Check if the device exists
                c.execute("SELECT * FROM devices WHERE device_id = ? AND device_type = ?",
                          (device_id,device_type))
                device_exists = c.fetchall()
                # Check if the rental log exists
                c.execute("SELECT * FROM device_logs WHERE device_id = ? and device_type = ?",
                          (device_id,device_type))
                rental_log_exists = c.fetchall()
                if rental_log_exists:
                    return render_template('message.html', message="Device already being rented. Please choose another device", loginstatus=loginstatus, message_btn="Try_Again",message_link="new-item")
                elif device_exists:
                    
                    #update student_data table
                    c.execute("SELECT * FROM student_data WHERE student_name = ?", (student_name,))
                    student_exists = c.fetchall()
                    if student_exists:
                        c.execute("UPDATE student_data SET last_rental = ?, device_type = ?, device_id = ? AND outstanding_rental = ? ", (date_borrowed, device_id, device_type, "YES"))
                    else: 
                        #deprecated if check --> no longer necessary
                        #c.execute("SELECT num_rentals FROM student_data WHERE student_name = ?", (student_name,))
                        #is_null = c.fetchone()

                        #if is_null[0] is None:
                        #    c.execute("UPDATE student_data SET num_rentals = 0 WHERE student_name = ?", (student_name,))                        
                        c.execute("INSERT INTO student_data(homeroom, student_name,num_rentals, last_rental, device_id, device_type, outstanding_rental) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (homeroom, student_name, 0, date_borrowed, device_id, device_type, "Yes"))
                    c.execute("UPDATE student_data SET num_rentals = num_rentals + 1 WHERE student_name = ?", (student_name,))
                    #update devices table
                    c.execute("UPDATE devices SET in_circulation = ? WHERE device_id = ? and device_type = ? ", ("Yes",device_id, device_type,))
                    #update device logs table
                    c.execute("INSERT INTO device_logs (date_borrowed, submitted_under, student_name, homeroom, device_type, device_id, period_borrowed, reason_borrowed, period_returned, teacher_signoff, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                              (date_borrowed, submitted_under, student_name, homeroom, device_type, device_id, period_borrowed, reason_borrowed, period_returned, teacher_signoff, notes))


                    return render_template('message.html', message="Successful Rental", loginstatus=loginstatus, message_btn="View_Rental_Logs",message_link="rental-logs")
                elif device_exists is None:
                    return render_template('message.html', message="Device doesn't exist. Please select a device that exists.", loginstatus=loginstatus, message_btn="Try_Again",message_link="new-log")
                else:
                    return render_template('message.html', message="Issue with renting a device. Please try again", loginstatus=loginstatus, message_btn="Try_Again",message_link="new-log")

            else:
                return render_template('new_log.html', loginstatus=loginstatus)
        else:
            return render_template('message.html', message="Please login to access this feature", message_btn="Login",message_link="login-page")

#Used for creating a new device
@app.route('/new-item')
@app.route('/new-item', methods=['POST'])
def new_item():
    with opendb('logs.db') as c:
        if request.method == "POST": #when user clicks submit button
            loginstatus = session['logged_in']

            #used for creating a new device
            device_id = request.form['device_id'] #may be replaced by a unique qr code instead of an id 
            device_type = request.form['device_type']
            # checks whether or not the device already exists
            c.execute('SELECT * from devices where device_type = ? and device_id = ?',(device_type, device_id))
            device_exists_check = c.fetchone()
            if device_exists_check is None:
                #get relevant data for writing to database
                date_submitted = datetime.datetime.now().strftime("%d-%m %H:%M") #records date and time device was created
                submitted_by = session['user_id']
                notes_device = request.form['notes']
                in_circulation = "No"

                # generate barcode image for device
                code128 = barcode.get_barcode_class('code128')
                barcode_image = code128(str(device_type) + " " + str(device_id), writer=ImageWriter())
                barcode_buffer = BytesIO()
                barcode_image.write(barcode_buffer)
                barcode_data = barcode_buffer.getvalue()

                # insert device data into database
                c.execute("INSERT INTO devices (device_id, device_type, date_added, added_by, in_circulation, notes, barcode, num_rentals) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (device_id, device_type, date_submitted, submitted_by, in_circulation, notes_device, barcode_data, 0))

                return render_template('message.html', message="New device logged", loginstatus=loginstatus, message_btn="View_Devices",message_link="device-logs")
            elif device_exists_check:
                return render_template('message.html', message="Device already exists", loginstatus=loginstatus, message_btn="Try_Again",message_link="new-item")   
            else:
                return render_template('message.html', message="An unknown error occured. Please try again", loginstatus=loginstatus, message_btn="Try_Again",message_link="new-item") 
        else:
            return render_template('new_device.html')
        
#Temporary dev admin page used to display all possible links
@app.route('/dev-admin', methods=['GET', 'POST'])
def dev_admin():
    if request.method == "POST":
        session['logged_in'] = True
        session['user_id'] = "Force_Login"
        return render_template('message.html', message="Successful force login", message_btn="Real_Login",message_link="login-page")
    else:
        loginstatus = session.get('logged_in', False)
        return render_template('dev_admin.html', loginstatus=loginstatus)

#Admin page
@app.route('/admin')
def admin():
    return render_template('/admin.html')


#Used to log the user out
@app.route('/logout', methods=["GET", "POST"])
def logout():
    if 'logged_in' in session and session['logged_in']:
        #setting login status and user id to False and invalid, respectfully
        session['logged_in'] = False
        session['user_id'] = "Invalid"
        loginstatus = session['logged_in']
        return render_template('/message.html', message="You have been logged out", loginstatus=loginstatus, message_btn="Login",message_link="login-page")
    else:
        session['logged_in'] = False
        session['user_id'] = "Invalid"
        loginstatus = session['logged_in']
        return render_template('/message.html', message="You are already not logged in", loginstatus=loginstatus, message_btn="Login",message_link="login-page")

#Used for loggin the user in
@app.route('/login-page')
def login_page():
    loginstatus = session['logged_in']
    return render_template('/login_page.html', loginstatus=loginstatus)

#used in conjunction with login page to update login related variables
def login_success(teacher_name, last_login):
    with opendb('main.db') as c:
        c.execute("SELECT logins FROM users WHERE teacher_name = ?", (teacher_name,))
        c.execute("UPDATE users SET logins = logins + 1 WHERE teacher_name = ?", (teacher_name,))
        #updates number of successful logins for a teacher
        c.execute("UPDATE users SET last_login = ? WHERE teacher_name = ?", (last_login, teacher_name))
        #sets last_login value to current date and time 

#login page post that confirms user details and then logs them in
@app.route('/login-page', methods=['POST'])
def login_page_post():
    with opendb('main.db') as c:
        teacher_name = request.form['teacher_name']
        passkey = request.form['password']
        c.execute('SELECT teacher_name,password FROM users WHERE teacher_name = ?', (teacher_name,))
        user = c.fetchone()
        #passkey = decoded password with hash and salt
        #checks if the user data is correct
        if user[0] == teacher_name and user[1] == passkey:
            session['logged_in'] = True
            session['user_id'] = teacher_name
            last_login = datetime.datetime.now().strftime("%d-%m %H:%M")
            login_success(teacher_name, last_login)
            loginstatus = session.get('logged_in', False)
            return render_template('message.html', message='Login Success', loginstatus=loginstatus, message_btn="Admin_Page",message_link="admin")
        else:
            session['logged_in'] = False
            session['user_id'] = 'Invalid'
            loginstatus = session.get('logged_in', False)
            return render_template('message.html', message='Login Failure', loginstatus=loginstatus, message_btn="Login",message_link="login-page")
        
def is_valid_email(email):
    """
    Check if the email address is valid.
    """
    # Regular expression for email validation
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None


@app.route('/signup-page')
def signup_page():
    loginstatus = session['logged_in']
    return render_template('/signup_page.html', loginstatus=loginstatus)

#used to create a new account
@app.route('/signup-page', methods=['POST'])
def signup_page_post():
    with opendb('main.db') as c:

        if request.method == 'POST':
            teacher_name = request.form['teacher_name']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm_password']

            # Check if teacher name already exists in the database
            c.execute('SELECT * FROM users WHERE teacher_name = ?', (teacher_name,))
            user = c.fetchone()
            if user:
                message = 'Teacher name already exists!'
                return render_template('message.html', message=message, message_btn="Sign_Up",message_link="signup-page")

            # Check if email is valid and not already in the database
            c.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = c.fetchone()
            if not is_valid_email(email):
                message = 'Invalid email address!'
                return render_template('message.html', message=message, message_btn="Sign_Up",message_link="signup-page")
            elif user:
                message = 'Email already exists!'
                return render_template('message.html', message=message, message_btn="Sign_Up",message_link="signup-page")

            # Check if password and confirm_password match
            if password != confirm_password:
                message = 'Passwords do not match!'
                return render_template('message.html', message=message, message_btn="Sign_Up",message_link="signup-page")

            # Hash the password and insert the user into the database
            salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
            hash_password = 'blablah'
            hashed_password = hash_password(password, salt)
            last_login = datetime.datetime.now().strftime("%d-%m %H:%M")
            c.execute('INSERT INTO users (teacher_name, email, password, salt, logins, date_created, last_login) VALUES (?, ?, ?, ?, ?, ?, ?)',
                          (teacher_name, email, hashed_password, salt, 0, "N/A", last_login))
            message = 'Sign up successful!'
            loginstatus = session['logged_in']
            return render_template('message.html', message=message, loginstatus=loginstatus , message_btn="Login",message_link="login-page")
        else:
            loginstatus = session['logged_in']
            return render_template('/signup_page.html', loginstatus=loginstatus)





#Custom message page
@app.route('/message')
def message():
    loginstatus = session['logged_in']
    return render_template('message.html', loginstatus=loginstatus, message_btn="View_Rental_Logs",message_link="rental-logs/", message="Message Page")


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

