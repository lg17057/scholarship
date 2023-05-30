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


# Home page
@app.route('/')
def main():
    session.setdefault('logged_in', False)
    session.setdefault('user_id', "Invalid")

    with opendb('logs.db') as c:
        loginstatus = session['logged_in']
        # if loginstatus is true display data
        #if loginstatus does not exist (aka program has just been launched), set loginstatus to false
        #fixes issues with keyError = none when program is first launched and certain pages are accessed
        if loginstatus is True:
            today = date.today()
            formatted_date = today.strftime("%d-%m")
            #SUBSTR date_borrowed, 1,5 takes the first 5 characters "dd-mm" from the date borrowed column
            #this ensures that formatted_date and formatted_yesterday will not take the time a device was rented
            #therefore ensuries that displayed data is from today
            c.execute("SELECT COUNT(*) FROM device_logs WHERE SUBSTR(date_borrowed, 1, 5) = ?",(formatted_date,))
            row1_descriptor = c.fetchone()[0]
            #total rentals today
            c.execute("SELECT COUNT(*) FROM device_logs WHERE SUBSTR(date_borrowed, 1, 5) = ? AND period_returned NOT IN ('Not Returned')",(formatted_date,))
            row2_descriptor = c.fetchone()[0]
            #devices returned today
            c.execute("SELECT COUNT(*) FROM device_logs WHERE SUBSTR(date_borrowed, 1, 5) = ? and teacher_signoff = ?",(formatted_date,"Confirmed"))
            row3_descriptor = c.fetchone()[0]
            #devices confirmed as returned today
            #takes the value of today any removes 1 day from it
            yesterday = date.today() - timedelta(days=1)
            formatted_yesterday = yesterday.strftime("%d-%m")
            #formates date to dd-mm format 
            c.execute("SELECT date_borrowed, device_type, device_id, student_name, homeroom, period_borrowed FROM device_logs WHERE SUBSTR(date_borrowed, 1, 5) = ? AND SUBSTR(date_borrowed, 1, 5) < ? AND period_returned = 'Not Returned'", (formatted_yesterday, date.today()))
            rows = c.fetchall()
            #selects all devices that are overdue (takes all values from date_borrowed value of formatted_yesterday and earlier)
            c.execute("SELECT date_borrowed, device_type, device_id, student_name, homeroom, period_borrowed FROM device_logs WHERE SUBSTR(date_borrowed, 1, 5) = ? AND period_returned = ? AND teacher_signoff = ?", (formatted_date,"Not Returned","Unconfirmed"))
            row1 = c.fetchall()
            #selects all devices that have been rented today
            return render_template('/index.html', row1_descriptor=row1_descriptor, row2_descriptor=row2_descriptor, row3_descriptor=row3_descriptor, message="Index Page", loginstatus=loginstatus, rows=rows, row1=row1)
        else:
            session['logged_in'] = False
            session['user_id'] = "Invalid"
            return render_template('/index.html', message="Index Page. Please login to access data", loginstatus=loginstatus)


#device log page
@app.route('/device-logs')
def device_logs():
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:
            c.execute("SELECT device_id, device_type, date_added, added_by, in_circulation, num_rentals, notes, last_rental FROM devices")
            rows = c.fetchall()
            loginstatus = session['logged_in']
            return render_template('/device_logs.html', rows=rows, loginstatus=loginstatus, message="Current devices")
        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
        #selects all device logs data
        

#used to provide link for the device barcode;
#format example; /barcode/Chromebook/2231
@app.route('/barcode/<string:device_type>/<int:device_id>')
def get_barcode(device_type, device_id):
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:
            c.execute('SELECT barcode FROM devices WHERE device_id = ? and device_type = ?', (device_id,device_type,))
            barcode_data = c.fetchone()[0]
            return Response(barcode_data, mimetype='image/png')
        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
        


#Page dedicated for the ability to modify devices and relevant data
@app.route('/modify-device')
def modify_device():
    status = session["logged_in"]
    if status is True:
        return render_template('modify_devices.html')
    else:
        message = "Please login to access this feature"
        return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
    


#page used to view current circulating devices that have NOT been returned
@app.route('/circulations')
def circulations():
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:
            today = date.today()       
            formatted_date = today.strftime("%d-%m")
     
            ipads_circulating = 'None circulating'
            chromebooks_circulating = 'None circulating'
            laptops_circulating = 'None circulating'
            # Finding the number of each device type that is in circulation; key in_circulation Yes
            c.execute("SELECT COUNT(*) FROM devices WHERE device_type='iPad' AND in_circulation='Yes' AND SUBSTR(last_rental, 1, 5) = ?", (formatted_date,))
            ipads_circulating = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM devices WHERE device_type='Chromebook' AND in_circulation='Yes' AND SUBSTR(last_rental, 1, 5) = ?", (formatted_date,))
            chromebooks_circulating = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM devices WHERE device_type='Laptop' AND in_circulation='Yes' AND SUBSTR(last_rental, 1, 5) = ?", (formatted_date,))
            laptops_circulating = c.fetchone()[0]
            # Selecting only devices that are currently in circulation --> combines data from different
            c.execute("SELECT date_borrowed, device_type, device_id, student_name, homeroom, period_borrowed FROM device_logs WHERE SUBSTR(date_borrowed, 1, 5) = ? AND period_returned = ? AND teacher_signoff = ?", (formatted_date,"Not Returned","Unconfirmed"))
            circulating_data = c.fetchall()
            return render_template('circulations.html', ipads_c=ipads_circulating, chromebooks_c=chromebooks_circulating,
                                   laptops_c=laptops_circulating, rows=circulating_data, status=status)
        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
        # The below section is proof of concept. The ipads, chromebooks, and laptops_circulating variables will become dynamic
       



@app.route('/overdues')
def overdue_rentals():
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:    
            formatted_date = date.today().strftime("%d-%m")
            yesterday = date.today() - timedelta(days=1) #SUBSTR(date_borrowed, 1, 5) = ? AND SUBSTR(date_borrowed, 1, 5) < ? 
            formatted_yesterday = yesterday.strftime("%d-%m")
            c.execute("SELECT * FROM device_logs WHERE period_returned = 'Not Returned' AND teacher_signoff = 'Unconfirmed' AND SUBSTR(date_borrowed, 1, 5) < ?", (formatted_date,))
            rows = c.fetchall()
            print('datata')
            print(rows)
            return render_template('overdues.html', loginstatus=status, rows=rows, message="Viewing Overdue Rentals")

        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")



#Page designed for data on students
@app.route('/student-data')
def student_data():
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:    

            student_total = c.execute("SELECT COUNT(*) FROM student_data")
            student_total = c.fetchone()
            student_total = str(student_total).strip("[]''()'',")


            rows = c.execute("SELECT * FROM student_data")
            rows = c.fetchall()

            return render_template('students.html', loginstatus=status, students_total=student_total, rows=rows)

        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")



#Displays all rental logs in a table 
#user can select what data of rental logs to see;
#example of date specific viewing; /rental-logs/11-04 
@app.route('/rental-logs/<string:date>')
def rental_logs_date(date):
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:
            c.execute("SELECT * FROM device_logs WHERE date_borrowed LIKE ?", (f"%{date}%",))
            rows = c.fetchall()
            loginstatus = session['logged_in']
            if not re.match(r'\d{2}-\d{2}', date):
                # checks for any invalid date format
                return render_template('rental_logs.html',rows=rows, message="Invalid date format. Please use dd-mm format.", loginstatus=loginstatus )
            return render_template('rental_logs.html', rows=rows, message="Viewing rental logs for {}".format(date), loginstatus=loginstatus)
        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
        


@app.route('/rental-logs/', methods=['GET', 'POST'])
def rental_logs():
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:
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
        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
        


#page for user to view device specific rental logs 
#example of route;  /rental-logs/2231
@app.route('/rental-logs/<string:device_type>/<int:device_id>')
def date_id_logs(device_type, device_id):
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:
            c.execute("SELECT * from device_logs WHERE device_type = ? AND device_id = ?", (device_type, device_id,))
            rows = c.fetchall()
            loginstatus = session['logged_in']
            message = "Viewing rental logs for {} ID {}".format(device_type, device_id)
            return render_template('rental_logs.html', loginstatus=loginstatus, rows=rows, message=message)
        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
       


#page or user to view device type specific rental logs without an ID
@app.route('/rental-logs/<string:device_type>/')
def device_type_logs(device_type):
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:
            c.execute("SELECT * FROM device_logs WHERE device_type = ?",(device_type,))
            rows = c.fetchall()
            loginstatus = session['logged_in']
            message = "Viewing rental logs for {}s".format(device_type)
            return render_template('rental_logs.html', loginstatus=loginstatus, rows=rows, message=message)
        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
        


#used to check whether or not the data for a date works
@app.route('/check-data/<string:date>')
def check_data_availability(date):
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:
            c.execute("SELECT COUNT(*) FROM device_logs WHERE date_borrowed LIKE ?", (f"%{date}%",))
            count = c.fetchone()[0]
            return jsonify({"exists": count > 0})
        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
        


#note for when device logs page is next developed
#add device,student and admin download ability and buttons to html page
#make it so that the date is actually properly sent to the python file instead of being saved as None in the file name
#let user save data from _date_ to _date_
@app.route('/download-logs/', methods=['GET','POST'])
def download_logs():
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:
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
                return render_template('/download_logs.html', loginstatus=loginstatus, message="Download Data" )
            return render_template('/download_logs.html', loginstatus=loginstatus, message="Download Data" )

        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
        

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
        status = session["logged_in"]
        if status is True:
        #selects all data from rental logs where data is unconfirmed
            c.execute("SELECT device_id, date_borrowed, submitted_under, student_name, homeroom, period_borrowed, reason_borrowed, period_returned, notes FROM device_logs WHERE teacher_signoff='Unconfirmed' AND period_returned IN (1, 2, 3, 4, 5, 6) AND period_returned != 'Not Returned'")
            rows = c.fetchall()
            loginstatus = session['logged_in']
            return render_template('sign_off.html', rows=rows, loginstatus=loginstatus, message="Viewing unconfirmed circulations")
        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
            


#Used to sign off a device based off of id; 
#can be used to rectify an issue where a device is trying to be rented and has not been confirmed as returned
@app.route('/sign-off/<string:device_type>/<int:device_id>')
def sign_off_deviceid(device_type,device_id):
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:
            c.execute('SELECT * FROM device_logs WHERE device_type = ? AND device_id = ? AND teacher_signoff = "Unconfirmed" AND period_returned NOT IN ("Not Returned")', (device_type, device_id,))
            rows = c.fetchall()
            loginstatus = session['logged_in']
            return render_template('/device_modifier.html', loginstatus=loginstatus, rows=rows, message="Sign Off Device ID {}".format(device_id))
        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
                


#Link that confirms entries after devices have been selected to sign off
@app.route('/confirm-entries', methods=['POST'])
def confirm_entries():
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:
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

        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
        


@app.route('/new-log')
@app.route('/new-log', methods=['POST'])
def new_log():
    # Open connection to the database
    with opendb('logs.db') as c:

        # Check if the user is logged in
        status = session["logged_in"]
        available_devices = c.execute("SELECT * FROM devices WHERE in_circulation = ?", ("No",))
        if status is True:
            if request.method == "POST":
                form_type = request.form.get('form_type')
                device_type = request.form.get('device_type')

                # Retrieve form data
                today = date.today()
                formatted_date = today.strftime("%d-%m")
                student_name = request.form.get('student_name')
                student_id = request.form.get('student_id')
                homeroom = request.form.get('homeroom')
                device_id = request.form.get('device_id')
                submitted_under = session['user_id']
                teacher_signoff = "Unconfirmed"
                current_date = date.today().strftime("%d-%m %H:%M")


                if form_type == "rent":
                    period_borrowed = request.form.get('period_borrowed')
                    reason_borrowed = request.form.get('reason_borrowed')
                    notes = request.form.get('notes') or "No notes"

                    if not available_devices:
                        return render_template('message.html', message=f"No {device_type}s available for rent", loginstatus=status, message_btn="Try_Again", message_link="new-log")

                    # Update student_data table
                    c.execute("SELECT * FROM student_data WHERE student_name = ?", (student_name,))
                    student_exists = c.fetchall()

                    if student_exists:
                        c.execute("UPDATE student_data SET last_rental = ?, device_type = ?, device_id = ?, outstanding_rental = ? WHERE student_name = ?",
                        (current_date, device_type, device_id, "Yes", student_name))
                    else:
                        c.execute("INSERT INTO student_data(homeroom, student_name, num_rentals, last_rental, device_id, device_type, outstanding_rental, student_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                  (homeroom, student_name, 0, date, device_id, device_type, "Yes", student_id))

                    c.execute("UPDATE student_data SET num_rentals = num_rentals + 1 WHERE student_name = ?", (student_name,))

                    # Update devices table
                    c.execute("UPDATE devices SET in_circulation = ?, last_rental = ? WHERE device_id = ? AND device_type = ?",
                    ("Yes", formatted_date, device_id, device_type))


                    # Update device logs table
                    c.execute("INSERT INTO device_logs (date_borrowed, submitted_under, student_name, homeroom, device_type, device_id, period_borrowed, reason_borrowed, period_returned, teacher_signoff, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (current_date, submitted_under, student_name, homeroom, device_type, device_id, period_borrowed, reason_borrowed, "Not Returned", "Unconfirmed", notes))

                    return render_template('message.html', message="Successful Rental", loginstatus=status, message_btn="View_Rental_Logs", message_link="rental-logs")
                elif form_type == "rent_scan":
                    barcode_input = request.form.get('barcode_input')
                    id_input = request.form.get('id_input')
                    period_borrowed = request.form.get('period_borrowed')
                    reason_borrowed = request.form.get('reason_borrowed')
                    notes = request.form.get('notes') or "No notes"
                    student_name = "ScannedID"
                    student_id = "ScannedID"
                    device_type, device_id = barcode_input.split('-')
                    print(device_type)
                    print(device_id)
                    if not available_devices:
                        return render_template('message.html', message=f"No {device_type}s available for rent", loginstatus=status, message_btn="Try_Again", message_link="new-log")

                    # Update student_data table
                    c.execute("SELECT * FROM student_data WHERE student_name = ?", (student_name,))
                    student_exists = c.fetchall()

                    if student_exists:
                        c.execute("UPDATE student_data SET last_rental = ?, device_type = ?, device_id = ?, outstanding_rental = ? WHERE student_name = ?",
                                  (date, device_type, device_id, "Yes", student_name))
                    else:
                        c.execute("INSERT INTO student_data (homeroom, student_name, student_id, num_rentals, last_rental, device_id, device_type, outstanding_rental, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                  (homeroom, student_name, student_id, 0, date, device_id, device_type, "Yes", notes))

                    c.execute("UPDATE student_data SET num_rentals = num_rentals + 1 WHERE student_name = ?", (student_name,))

                    # Update devices table
                    c.execute("UPDATE devices SET in_circulation = ? AND last_rental WHERE device_id = ? AND device_type = ?",
                              ("Yes",formatted_date, device_id, device_type))

                    # Update device logs table
                    c.execute("INSERT INTO device_logs (date_borrowed, submitted_under, student_name, homeroom, device_type, device_id, period_borrowed, reason_borrowed, period_returned, teacher_signoff, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                              (date, submitted_under, student_name, homeroom, device_type, device_id, period_borrowed, reason_borrowed, "Not Returned", teacher_signoff, notes))

                    return render_template('message.html', message="Successful Rental", loginstatus=status, message_btn="View_Rental_Logs", message_link="rental-logs")
                elif form_type == "return":
                    period_returned = request.form.get('period_returned')
                    notes = request.form.get('notes') or "No notes"

                    # Check if the device exists
                    c.execute("SELECT * FROM devices WHERE device_id = ? AND device_type = ?", (device_id, device_type))
                    device_exists = c.fetchall()

                    if not device_exists:
                        return render_template('message.html', message="Device doesn't exist. Please select a device that exists.", loginstatus=status, message_btn="Try_Again", message_link="new-log")

                    # Check if the rental log exists
                    c.execute("SELECT * FROM device_logs WHERE device_id = ? AND device_type = ? AND teacher_signoff = ? AND period_returned = ?",
                              (device_id, device_type, "Unconfirmed", "Not Returned"))
                    rental_log_exists = c.fetchall()

                    if not rental_log_exists:
                        return render_template('message.html', message="Rental Log does not exist. Please choose another device", loginstatus=status, message_btn="Try_Again", message_link="new-log")

                    # Update student_data table
                    c.execute("SELECT * FROM student_data WHERE student_name = ?", (student_name,))
                    student_exists = c.fetchall()

                    if student_exists:
                        c.execute("UPDATE student_data SET last_rental = ?, device_type = ?, device_id = ?, outstanding_rental = ? WHERE student_name = ?",
          (current_date, device_type, device_id, "No", student_name))

                    else:
                        return render_template('message.html', message="Student has no outstanding rentals", loginstatus=status, message_btn="Return_Device", message_link="new-log")

                    # Update devices table
                    c.execute("UPDATE devices SET in_circulation = ? WHERE device_id = ? AND device_type = ?",
                              ("No", device_id, device_type,))

                    c.execute("UPDATE device_logs SET period_returned = ?, notes = ? WHERE device_id = ? AND device_type = ?",
                              (period_returned, notes, device_id, device_type))

                    return render_template('message.html', message="Device Returned", loginstatus=status, message_btn="View_Rental_Logs", message_link="rental-logs")
                elif form_type == "return_scan":
                    period_returned = request.form.get('period_returned')
                    notes = request.form.get('notes') or "No notes"

                    # Check if the device exists
                    c.execute("SELECT * FROM devices WHERE device_id = ? AND device_type = ?", (device_id, device_type))
                    device_exists = c.fetchall()

                    if not device_exists:
                        return render_template('message.html', message="Device doesn't exist. Please select a device that exists.", loginstatus=status, message_btn="Try_Again", message_link="new-log")

                    # Check if the rental log exists
                    c.execute("SELECT * FROM device_logs WHERE device_id = ? AND device_type = ? AND teacher_signoff = ? AND period_returned = ?",
                              (device_id, device_type, "Unconfirmed", "Not Returned"))
                    rental_log_exists = c.fetchall()

                    if not rental_log_exists:
                        return render_template('message.html', message="Rental Log does not exist. Please choose another device", loginstatus=status, message_btn="Try_Again", message_link="new-log")

                    # Update student_data table
                    c.execute("SELECT * FROM student_data WHERE student_name = ?", (student_name,))
                    student_exists = c.fetchall()

                    if student_exists:
                        c.execute("UPDATE student_data SET last_rental = ?, device_type = ?, device_id = ?, outstanding_rental= ? WHERE student_name = ?",
                                  (date, device_type, device_id, "No", student_name))
                    else:
                        return render_template('message.html', message="Student has no outstanding rentals", loginstatus=status, message_btn="Return_Device", message_link="new-log")

                    # Update devices table
                    c.execute("UPDATE devices SET in_circulation = ? WHERE device_id = ? AND device_type = ?",
                              ("No", device_id, device_type,))

                    c.execute("UPDATE device_logs SET period_returned = ?, notes = ? WHERE device_id = ? AND device_type = ?",
                              (period_returned, notes, device_id, device_type))

                    return render_template('message.html', message="Device Returned", loginstatus=status, message_btn="View_Rental_Logs", message_link="rental-logs")
            else:
                return render_template('new_log.html', status=status, available_devices=available_devices)

        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login", message_link="login-page")        


#Used for creating a new device
@app.route('/new-item')
@app.route('/new-item', methods=['POST'])
def new_item():
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:
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
                    c.execute("INSERT INTO devices (device_id, device_type, date_added, added_by, in_circulation, notes, barcode, num_rentals, last_rental) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (device_id, device_type, date_submitted, submitted_by, in_circulation, notes_device, barcode_data, 0, "Invalid"))
                    return render_template('message.html', message="New device logged", loginstatus=loginstatus, message_btn="View_Devices",message_link="device-logs")
                elif device_exists_check:
                    return render_template('message.html', message="Device already exists", loginstatus=loginstatus, message_btn="Try_Again",message_link="new-item")   
                else:
                    return render_template('message.html', message="An unknown error occured. Please try again", loginstatus=loginstatus, message_btn="Try_Again",message_link="new-item") 
            else:
                return render_template('new_device.html')
        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
        
        

#Temporary dev admin page used to display all possible links
@app.route('/dev-admin', methods=['GET', 'POST'])
def dev_admin():
    status = session["logged_in"]
    if status is True:
        if request.method == "POST":
            session['logged_in'] = True
            session['user_id'] = "Force_Login"
            return render_template('message.html', message="Successful force login", message_btn="Real_Login",message_link="login-page")
        else:
            loginstatus = session.get('logged_in', False)
            return render_template('dev_admin.html', loginstatus=loginstatus)
    else:
        message = "Please login to access this feature"
        return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
    


#Admin page
@app.route('/admin')
def admin():
    status = session["logged_in"]
    if status is True:
        return render_template('/admin.html')
    else:
        message = "Please login to access this feature"
        return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
    


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
    loginstatus = session['logged_in']
    if loginstatus:
        return render_template('/message.html', loginstatus=loginstatus,  message_btn="View_Logs",message_link="rental-logs", message="You are already logged in")
    else:
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
        status = session["logged_in"]
        if status is True:
            if request.method == "POST":
                teacher_name = request.form['teacher_name']
                email = request.form['email']
                passkey = request.form['password']
                c = c.execute('SELECT teacher_name FROM users WHERE teacher_name=? OR email=?', (teacher_name, email,))
                user_check = c.fetchone()
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

        else:
            message = "Please login as an admin to create new admin account"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
       

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



