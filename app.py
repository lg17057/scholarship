#general imports for flask
from flask import Flask, render_template, url_for, redirect, request, make_response, jsonify, session, Response, send_file
from barcode.writer import ImageWriter
from datetime import date, timedelta
from barcode import EAN13
from select import select
from io import BytesIO
from time import sleep
import sqlite3 as sql
from sqlite3 import *
import datetime
import barcode
import bcrypt
import time
import csv
import re

#defines static file path
app = Flask(__name__, static_url_path='/static')   
#randomly generates secret key for sessions
app.secret_key = 'ajnasdN&aslpo0912nlasiqwenz'


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
    with opendb('logs.db') as c:
        loginstatus = session['logged_in']
        if loginstatus:
            today = date.today()
            formatted_date = today.strftime("%d-%m")
            c.execute("SELECT COUNT(*) FROM device_logs WHERE date_borrowed = ?",(formatted_date,))
            row1_descriptor = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM device_logs WHERE date_borrowed = ? AND period_returned NOT IN ('Not Returned')",(formatted_date,))
            row2_descriptor = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM device_logs WHERE date_borrowed = ? and teacher_signoff = ?",(formatted_date,"Confirmed"))
            row3_descriptor = c.fetchone()[0]

            yesterday = date.today() - timedelta(days=1)
            formatted_yesterday = yesterday.strftime("%d-%m")
            
            c.execute("SELECT date_borrowed, device_type, device_id, student_name, homeroom, period_borrowed FROM device_logs WHERE date_borrowed = ? AND date_borrowed < ?", (formatted_yesterday, date.today()))
            rows = c.fetchall()
            return render_template('/index.html', row1_descriptor=row1_descriptor, row2_descriptor=row2_descriptor, row3_descriptor=row3_descriptor, message="Index Page", loginstatus=loginstatus, rows=rows)
        else:
            session['logged_in'] = False
            session['user_id'] = False
            return render_template('/index.html', message="Index Page", loginstatus=loginstatus)


#device log page
@app.route('/device-logs')
def device_logs():
    with opendb('logs.db') as c:
        #selects all device logs data
        c.execute("SELECT * FROM devices ")
        rows = c.fetchall()
        loginstatus = session['logged_in']
        return render_template('/device_logs.html', rows=rows, loginstatus=loginstatus, message="Current devices")


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
        if not re.match(r'\d{2}-\d{2}', date):
            # checks for any invalid date format
            return render_template('rental_logs.html',rows=rows, message="Invalid date format. Please use dd-mm format.", loginstatus=loginstatus )
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
        loginstatus = session['logged_in']
        message = "Viewing rental logs for {} ID {}".format(device_type, device_id)
        return render_template('rental_logs.html', loginstatus=loginstatus, rows=rows, message=message)


#page or user to view device type specific rental logs without an ID
@app.route('/rental-logs/<string:device_type>/')
def device_type_logs(device_type):
    with opendb('logs.db') as c:
        c.execute("SELECT * FROM device_logs WHERE device_type = ?",(device_type,))
        rows = c.fetchall()
        loginstatus = session['logged_in']
        message = "Viewing rental logs for {}s".format(device_type)
        return render_template('rental_logs.html', loginstatus=loginstatus, rows=rows, message=message)


#used to check whether or not the data for a date works
@app.route('/check-data/<string:date>')
def check_data_availability(date):
    with opendb('logs.db') as c:
        c.execute("SELECT COUNT(*) FROM device_logs WHERE date_borrowed LIKE ?", (f"%{date}%",))
        count = c.fetchone()[0]
        return jsonify({"exists": count > 0})


#note for when device logs page is next developed
#add device,student and admin download ability and buttons to html page
#make it so that the date is actually properly sent to the python file instead of being saved as None in the file name
#let user save data from _date_ to _date_
@app.route('/download-logs/', methods=['GET','POST'])
def download_logs():
    with opendb('logs.db') as c:
        loginstatus = session['logged_in']
        if request.method == 'POST':
                    device_type = request.form.get('devicepicker')
                    device_id = request.form.get('idpicker')
                    date_picker = request.form.get('datepicker')
                    rows = fetch_rows(device_type, device_id, date_picker)
                    if rows:
                        format_picker = request.form.get('formatpicker')
                        if format_picker == 'CSV':
                            csv_data = generate_csv(rows)
                            response = make_response(csv_data)
                            response.headers['Content-Disposition'] = 'attachment; filename=RentalLogs_{}_{}_{}.csv'.format(device_type, device_id, date_picker)
                            response.headers['Content-Type'] = 'text/csv'
                            return response
                        elif format_picker == 'PDF':
                            pdf_data = generate_pdf(rows)
                            response = make_response(pdf_data)
                            response.headers['Content-Disposition'] = 'attachment; filename=RentalLogs_{}_{}_{}.pdf'.format(device_type, device_id, date_picker)
                            response.headers['Content-Type'] = 'application/pdf'
                            return response
                        else: 
                            pass
                    else:
                        message = 'No data found for the specified criteria.'
                        return render_template('download_logs.html', loginstatus=loginstatus, message=message)
        else:        
            return render_template('/download_logs.html', loginstatus=loginstatus, message="Download All Rental Data" )
        return render_template('/download_logs.html', loginstatus=loginstatus, message="Download All Rental Data" )


def fetch_rows(device_type, device_id, date_picker):
    with opendb('logs.db') as c:
        print(device_type)
        print(device_id)
        print(date_picker)
        query = "SELECT * FROM device_logs WHERE device_type=? AND device_id=?"
        rows = c.execute(query, (device_type, device_id)).fetchall()
        return rows


def generate_csv(rows):
    headers = ["Date Borrowed", "Submitted Under", "Student Name", "Homeroom", "Device Type",
               "Device ID", "Period Borrowed", "Reason Borrowed", "Period Returned",
               "Teacher Sign-Off", "Notes"]
    csv_content = ','.join(headers) + '\n'
    for row in rows:
        csv_content += ','.join(str(value) for value in row) + '\n'
    return csv_content


def generate_pdf(rows):
    # Implement the logic to generate PDF data from the fetched rows
    # Return the PDF content as bytes
    pdf_content = b''
    # ... Your PDF generation logic here ...
    return pdf_content


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
    with opendb('logs.db') as c:
        device_ids = request.form.getlist('device_ids[]')
        loginstatus = session['logged_in']
        if device_ids:
            try:
                c.execute('UPDATE device_logs SET teacher_signoff = "Confirmed" WHERE device_id IN ({})'.format(','.join('?' * len(device_ids))), device_ids)
                message = 'Selected entries have been confirmed.'
                message_type = 'success'
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
                c.execute("SELECT * FROM device_logs WHERE device_id = ? and device_type = ? and teacher_signoff = ? and period_returned = ?",
                          (device_id,device_type,"Unconfirmed","Not Returned"))
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
    

@app.route('/login-page')
def login_page():
    loginstatus = session.get('logged_in', False)
    return render_template('/login_page.html', loginstatus=loginstatus)


def login_success(teacher_name, last_login):
    with opendb('main.db') as c:
        c.execute("SELECT logins FROM users WHERE teacher_name = ?", (teacher_name,))
        c.execute("UPDATE users SET logins = logins + 1 WHERE teacher_name = ?", (teacher_name,))
        c.execute("UPDATE users SET last_login = ?", (last_login,))


@app.route('/login-page', methods=["POST"])
def login_page_post():
    with opendb('main.db') as c:
        input_value = request.form['teacher_name'] 
        passkey = request.form['password']
        is_email = re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', input_value)
        if is_email:
            c.execute('SELECT * FROM users WHERE email=?', (input_value,))
        else:
            c.execute('SELECT * FROM users WHERE teacher_name=?', (input_value,))
        user_data = c.fetchone()
        if user_data:
            stored_password_bytes = user_data[3]  
            stored_salt_bytes = user_data[4]  
            stored_password = stored_password_bytes.decode('utf-8')
            stored_salt = stored_salt_bytes.decode('utf-8')
            if bcrypt.checkpw(passkey.encode('utf-8'), stored_password.encode('utf-8')):
                session['logged_in'] = True
                session['user_id'] = user_data[1]  # Assuming the username or email is at index 1
                last_login = datetime.datetime.now().strftime("%d-%m %H:%M")
                login_success(user_data[1], last_login)  # Assuming the username or email is at index 1
                loginstatus = session['logged_in']
                return render_template('message.html', message="Login Success", loginstatus=loginstatus, message_btn="Index_Page",message_link="")
        session['logged_in'] = False
        session['user_id'] = "Invalid"
        loginstatus = session['logged_in']
        return render_template('message.html', message="Login Failure", loginstatus=loginstatus, message_btn="Index_Page",message_link="")


@app.route('/signup-page')
def signup_page():
    loginstatus = session.get('logged_in', False)
    return render_template('/signup_page.html', loginstatus=loginstatus)


@app.route('/signup-page', methods=['POST'])
def signup_page_post():
    with opendb('main.db') as c:
        if request.method == "POST":
            teacher_name = request.form['teacher_name']
            email = request.form['email']
            passkey = request.form['password']
            cursor = c.execute('SELECT teacher_name FROM users WHERE teacher_name=? OR email=?', (teacher_name, email,))
            user_check = cursor.fetchone()
            if user_check: 
                loginstatus = session.get('logged_in', False)
                return render_template('message.html',
                                       message='Sign Up failure. User with the same name or email already exists.',
                                       loginstatus=loginstatus,  message_btn="Try_Again",message_link="signup-page")
            else:  
                now = datetime.datetime.now()
                date_created = now.strftime("%d-%m %H:%M")
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(passkey.encode('utf-8'), salt)
                # Store the salt and hashed password as bytes
                salt_bytes = salt
                hashed_password_bytes = hashed_password
                c.execute('INSERT INTO users (teacher_name, email, password, salt, logins, date_created, last_login) VALUES (?, ?, ?, ?, ?, ?, ?)',(teacher_name, email, hashed_password_bytes, salt_bytes, 0, date_created, "N/A"))
                loginstatus = session.get('logged_in', False)
                return render_template('message.html', message="Sign Up success", loginstatus=loginstatus, message_btn="Login",message_link="login-page")
        else:
            return render_template('signup_page.html', loginstatus=loginstatus)


#Custom message page
@app.route('/message')
def message():
    loginstatus = session['logged_in']
    return render_template('message.html', loginstatus=loginstatus, message_btn="View_Rental_Logs",message_link="rental-logs/", message="Message Page")


############################################# End-user oriented
# Help page
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



#camera = cv2.VideoCapture(0)
#
#def gen_frames():
#    while True:
#        success, frame = camera.read()  # Read the camera frame
#        if not success:
#            break
#        else:
#            # Convert the frame to grayscale for barcode detection
#            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#            # Detect barcodes in the grayscale frame
#            barcodes = pyzbar.decode(gray)
#
#            for barcode in barcodes:
#                # Extract the barcode data and type
#                barcode_data = barcode.data.decode("utf-8")
#                barcode_type = barcode.type
#
#                # Draw a rectangle around the barcode
#                (x, y, w, h) = barcode.rect
#                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
#
#                # Display the barcode data and type on the frame
#                cv2.putText(frame, f"{barcode_data} ({barcode_type})", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
#
#            # Convert the frame to JPEG format
#            ret, buffer = cv2.imencode('.jpg', frame)
#            frame = buffer.tobytes()
#
#            # Yield the frame for streaming
#            yield (b'--frame\r\n'
#                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#
#@app.route('/video_feed')
#def video_feed():
#    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Responsible for running the website
if __name__ == '__main__':
    app.run(debug="True")

