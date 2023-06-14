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
import random
import bcrypt
import time
import json
import csv
import re
############ PDF IMPORTS
from fpdf import FPDF
import os
from PIL import Image
import barcode
from barcode import Code128
from barcode.writer import ImageWriter






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



def get_device_list(c):
    device_list_query = "SELECT device_id, device_type FROM devices"
    c.execute(device_list_query)
    device_list = c.fetchall()
    device_ids = [device[0] for device in device_list]
    device_types = [device[1] for device in device_list]
    return device_ids, device_types

def get_uncirc_device_list(c):
    device_list_query = "SELECT device_id, device_type FROM devices WHERE in_circulation = 'No'"
    c.execute(device_list_query)
    device_list = c.fetchall()
    device_ids = [device[0] for device in device_list]
    device_types = [device[1] for device in device_list]
    return device_ids, device_types

# Home page
@app.route('/')
@app.route('/', methods=['GET','POST'])
def main():
    session.setdefault('logged_in', False)
    session.setdefault('user_id', "Invalid")
    with opendb('logs.db') as c:
        loginstatus = session['logged_in']
        status = session['logged_in']
        if loginstatus is True:

            available_devices = c.execute("SELECT * FROM devices WHERE in_circulation = ?", ("No",))
            # if loginstatus is true display data
            #if loginstatus does not exist (aka program has just been launched), set loginstatus to false
            #fixes issues with keyError = none when program is first launched and certain pages are accessed
            if request.method == "POST":
                form_type = request.form.get('form_type')
                device_type = request.form.get('device_type')
                # Retrieve form data
                formatted_date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")

                student_name = request.form.get('student_name')
                student_id = request.form.get('student_id')
                homeroom = request.form.get('homeroom')
                device_id = request.form.get('device_id')
                submitted_under = session['user_id']
                teacher_signoff = "Unconfirmed"
                current_date = date.today().strftime("%d-%m-%Y %H:%M")
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
                        (formatted_date, device_type, device_id, "Yes", student_name))
                    else:
                        c.execute("INSERT INTO student_data(homeroom, student_name, num_rentals, last_rental, device_id, device_type, outstanding_rental, student_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                  (homeroom, student_name, 0, date, device_id, device_type, "Yes", student_id))
                    c.execute("UPDATE student_data SET num_rentals = num_rentals + 1 WHERE student_name = ?", (student_name,))
                    # Update devices table
                    c.execute("UPDATE devices SET in_circulation = ?, last_rental = ? WHERE device_id = ? AND device_type = ?",
                    ("Yes", formatted_date, device_id, device_type))
                    # Update device logs table
                    c.execute("INSERT INTO device_logs (date_borrowed, submitted_under, student_name, homeroom, device_type, device_id, period_borrowed, reason_borrowed, period_returned, teacher_signoff, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (formatted_date, submitted_under, student_name, homeroom, device_type, device_id, period_borrowed, reason_borrowed, "Not Returned", "Unconfirmed", notes))
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
            
            today = date.today()
            formatted_date = today.strftime("%d-%m-%Y")
            dates = datetime.datetime.now().date().strftime("%d-%m-%yyyy")
            yesterday = date.today() - timedelta(days=1)
            formatted_yesterday = yesterday.strftime("%d-%m-%Y")
            #SUBSTR date_borrowed, 1,5 takes the first 5 characters "dd-mm" from the date borrowed column
            #this ensures that formatted_date and formatted_yesterday will not take the time a device was rented
            #therefore ensuries that displayed data is from today
            c.execute("SELECT date_borrowed FROM device_logs WHERE SUBSTR(date_borrowed, 1,10) = ?", (formatted_date,))
            rows = c.fetchall()
            row1_descriptor = len(rows)
            #total rentals today
            c.execute("SELECT date_borrowed FROM device_logs WHERE SUBSTR(date_borrowed, 1,10) = ? AND period_returned != 'Not Returned'", (formatted_date,))
            rows = c.fetchall()
            row2_descriptor = len(rows)
            #devices returned today
            c.execute("SELECT date_borrowed FROM device_logs WHERE SUBSTR(date_borrowed, 1,10) = ? AND teacher_signoff = 'Confirmed'", (formatted_date,))
            rows = c.fetchall()
            row3_descriptor = len(rows)
            c.execute("SELECT date_borrowed, device_type, device_id, student_name, homeroom, period_borrowed FROM device_logs WHERE date_borrowed <= ? AND teacher_signoff != ? AND SUBSTR(date_borrowed,1,5) != ?", (yesterday, "Confirmed", dates))
            rows = c.fetchall()
            row4_descriptor = len(rows)
            #devices confirmed as returned today
            #takes the value of today any removes 1 day from it
            
            device_ids, device_types = get_uncirc_device_list(c)
            # Convert the current date to the desired format
            c.execute("SELECT date_borrowed, device_type, device_id, student_name, homeroom, period_borrowed FROM device_logs WHERE date_borrowed <= ? AND teacher_signoff != ? AND SUBSTR(date_borrowed,1,5) != ?", (yesterday, "Confirmed", dates))
            rows = c.fetchall()
            
            #selects all devices that are overdue (takes all values from date_borrowed value of formatted_yesterday and earlier)
            c.execute("SELECT date_borrowed, device_type, device_id, student_name, homeroom, period_borrowed FROM device_logs WHERE SUBSTR(date_borrowed, 1,10) = ? AND period_returned = ? AND teacher_signoff = ?", (formatted_date,"Not Returned","Unconfirmed"))
            row1 = c.fetchall()
            #selects all devices that have been rented today
            return render_template('/index.html', row1_descriptor=row1_descriptor, row2_descriptor=row2_descriptor, row3_descriptor=row3_descriptor, row4_descriptor=row4_descriptor, message="Index Page", loginstatus=loginstatus, rows=rows, row1=row1, device_ids=device_ids, device_types=device_types)
        else:
            session['logged_in'] = False
            session['user_id'] = "Invalid"
            device_ids, device_types = get_device_list(c)
            return render_template('/index.html', message="Index Page. Please login to access data", loginstatus=loginstatus, device_ids=device_ids, device_types=device_types)



#device log page
@app.route('/device-logs')
def device_logs():
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:
            c.execute("SELECT device_id, device_type, date_added,last_change, added_by, in_circulation, num_rentals, notes, last_rental FROM devices")
            rows = c.fetchall()
            return render_template('/device_logs.html', rows=rows, loginstatus=status, message="Current devices", )
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
@app.route('/modify-device/<string:device_type>/<int:device_id>', methods=['POST','GET'])
def modify_device_selected(device_type, device_id):
    with opendb('logs.db') as c:
        status = session['logged_in']
        today = date.today()       
        formatted_date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
        c.execute("SELECT device_id, device_type, date_added, added_by, in_circulation, notes, num_rentals, last_rental, last_change FROM devices where device_type = ? AND device_id = ?", (device_type, device_id))
        data = c.fetchone()
        
        if data is None:
            message = "Device not found"
            return render_template('message.html', message=message, loginstatus=status, message_btn="View_Devices", message_link="device-logs")
        
        if request.method == "POST":
            form_type = request.form.get('form_type')
            
            if form_type == 'device-select':
                device_type_secondary = request.form.get('devicepicker')
                device_id_secondary = request.form.get('idpicker')
                return redirect('/modify-device/{}/{}'.format(device_type_secondary, device_id_secondary))
            
            elif form_type == 'device-mod':
                device_type_third = request.form.get('device_type')
                device_id_third = request.form.get('device_id')
                date_added = request.form.get('date_added')
                added_by = request.form.get('added_by')
                in_circulation = request.form.get('in_circulation')
                notes = request.form.get('notes')
                num = request.form.get('num_rentals')
                last_rental = request.form.get('last_rental')
                
                # Update devices table
                c.execute("UPDATE devices SET device_id = ?, device_type = ?, date_added = ?, last_change = ?, added_by = ?, in_circulation = ?, notes = ?, num_rentals = ?, last_rental = ? WHERE device_id = ? AND device_type = ?",
                (device_id_third, device_type_third, date_added, formatted_date, added_by, in_circulation, notes, num, last_rental, device_id, device_type))
                
                message = "Device data successfully updated"
                return render_template('message.html', message=message, loginstatus=status, message_btn="View_Devices", message_link="device-logs")
        
        device_ids, device_types = get_device_list(c)
        
        return render_template('modify_devices.html',modify_container_visible=True,id=data[0],type=data[1],added=data[2],added_by=data[3],circs=data[4],notes=data[5],num=data[6],last=data[7],last_change=data[8],loginstatus=status,message="Modifying {} {}".format(device_type, device_id),device_ids=device_ids,device_types=device_types)


@app.route('/modify-device', methods=['POST', 'GET'])
def modify_device():
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:
            if request.method == 'POST':
                device_type = request.form.get('devicepicker')
                device_id = request.form.get('idpicker')
                return redirect('/modify-device/{}/{}'.format(device_type, device_id))
            
            device_ids, device_types = get_device_list(c)
            
            return render_template('modify_devices.html', loginstatus=status, message="Select Device: ",modify_container_visible=False, device_ids=device_ids, device_types=device_types)
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
            formatted_date = today.strftime("%d-%m-%Y %H:M")
     
            ipads_circulating = 'None circulating'
            chromebooks_circulating = 'None circulating'
            laptops_circulating = 'None circulating'
            # Finding the number of each device type that is in circulation; key in_circulation Yes
            c.execute("SELECT COUNT(*) FROM devices WHERE device_type='iPad' AND in_circulation='Yes' AND SUBSTR(last_rental, 1, 8) = ?", (formatted_date,))
            ipads_circulating = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM devices WHERE device_type='Chromebook' AND in_circulation='Yes' AND SUBSTR(last_rental, 1, 8) = ?", (formatted_date,))
            chromebooks_circulating = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM devices WHERE device_type='Laptop' AND in_circulation='Yes' AND SUBSTR(last_rental, 1, 8) = ?", (formatted_date,))
            laptops_circulating = c.fetchone()[0]
            # Selecting only devices that are currently in circulation --> combines data from different
            c.execute("SELECT date_borrowed, device_type, device_id, student_name, homeroom, period_borrowed FROM device_logs WHERE SUBSTR(date_borrowed, 1, 8) = ? AND period_returned = ? AND teacher_signoff = ?", (formatted_date,"Not Returned","Unconfirmed"))
            circulating_data = c.fetchall()
            return render_template('circulations.html', ipads_c=ipads_circulating, chromebooks_c=chromebooks_circulating,
                                   laptops_c=laptops_circulating, rows=circulating_data, status=status)
        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
        # The below section is proof of concept. The ipads, chromebooks, and laptops_circulating variables will become dynamic
       

@app.route('/overdues', methods=['POST','GET'])
def overdue_rentals():
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:    
            formatted_date = date.today().strftime("%d-%m-%Y %H:M")
            yesterday = date.today() - timedelta(days=1) #SUBSTR(date_borrowed, 1, 5) = ? AND SUBSTR(date_borrowed, 1, 5) < ? 
            formatted_yesterday = yesterday.strftime("%d-%m-%Y %H:M")
            c.execute("SELECT * FROM device_logs WHERE period_returned = 'Not Returned' AND teacher_signoff = 'Unconfirmed' AND SUBSTR(date_borrowed, 1, 8) < ?", (formatted_date,))
            rows = c.fetchall()

            if request.method == 'POST':
                device_type = request.form.get('devicepicker')
                device_id = request.form.get('idpicker')
                return redirect('/overdues/{}/{}'.format(device_type, device_id))


            device_ids, device_types = get_device_list(c)

            return render_template('overdues.html', loginstatus=status,device_ids=device_ids,device_types=device_types, rows=rows, message="Viewing Overdue Rentals")

        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")


@app.route('/overdues/<string:device_type>/<int:device_id>')
def overdue_rentals_devicespecific(device_type,device_id):
     with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:    
            formatted_date = date.today().strftime("%d-%m-%Y %H:M")
            yesterday = date.today() - timedelta(days=1) #SUBSTR(date_borrowed, 1, 5) = ? AND SUBSTR(date_borrowed, 1, 5) < ? 
            formatted_yesterday = yesterday.strftime("%d-%m-%Y %H:M")
            c.execute("SELECT * FROM device_logs WHERE period_returned = 'Not Returned' AND teacher_signoff = 'Unconfirmed' AND SUBSTR(date_borrowed, 1, 8) < ? AND device_type = ? AND device_id = ?", (formatted_date,device_type,device_id,))
            rows = c.fetchall()
            device_ids, device_types = get_device_list(c)

            return render_template('overdues.html', loginstatus=status,device_ids=device_ids,device_types=device_types, rows=rows, message="Viewing Overdue Rentals")

        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")


#Page designed for data on students
@app.route('/student-data')
def student_data():
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:    
            loginstatus = session['logged_in']
            student_total = c.execute("SELECT COUNT(*) FROM student_data")
            student_total = c.fetchone()
            student_total = str(student_total).strip("[]''()'',")


            rows = c.execute("SELECT * FROM student_data")
            rows = c.fetchall()

            return render_template('students.html', loginstatus=loginstatus, students_total=student_total, rows=rows)

        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")


@app.route('/rental-logs/', methods=['GET', 'POST'])
def rental_logs():
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:
            today = date.today()
            formatted_date = today.strftime("%d-%m-%Y %H:M")
            c.execute("SELECT * from device_logs")
            logs = c.fetchall()
            c.execute("SELECT DISTINCT date_borrowed FROM device_logs")
            available_dates = [row[0] for row in c.fetchall()]


            if request.method == 'POST':
                device_type = request.form.get('devicepicker')
                device_id = request.form.get('idpicker')
                return redirect('/rental-logs/{}/{}'.format(device_type, device_id))
            device_ids, device_types = get_device_list(c)


            return render_template('rental_logs.html',device_ids=device_ids,device_types=device_types, rows=logs,available_dates=available_dates, message="Viewing all rental logs", formatted_date=formatted_date, loginstatus=status)
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
            device_ids, device_types = get_device_list(c)
            return render_template('rental_logs.html', loginstatus=status, rows=rows, message=message, device_ids=device_ids, device_types=device_types)
        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page") 


#page or user to view device type specific rental logs without an ID
#removed this route because of new form type and the user can sort the table anyways
#@app.route('/rental-logs/<string:device_type>/')
#def device_type_logs(device_type):
#    with opendb('logs.db') as c:
#        status = session["logged_in"]
#        if status is True:
#            c.execute("SELECT * FROM device_logs WHERE device_type = ?",(device_type,))
#            rows = c.fetchall()
#            loginstatus = session['logged_in']
#            message = "Viewing rental logs for {}s".format(device_type)
#            device_list_query = "SELECT device_id, device_type FROM devices WHERE in_circulation = 'No'"
#            c.execute(device_list_query)
#            device_list = c.fetchall()
#            device_ids = [device[0] for device in device_list]
#            device_types = [device[1] for device in device_list]
#            return render_template('rental_logs.html', loginstatus=status, rows=rows, message=message,device_ids=device_ids, device_types=device_types)
#        else:
#            message = "Please login to access this feature"
#            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
        
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
                return render_template('rental_logs.html',rows=rows, message="Invalid date format. Please use dd-mm format.", loginstatus=status )
            device_ids, device_types = get_device_list(c)
            return render_template('rental_logs.html', rows=rows, message="Viewing rental logs for {}".format(date), loginstatus=status, device_ids=device_ids, device_types=device_types)
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

@app.route('/download-logs/', methods=['GET', 'POST'])
def download_logs():
    with opendb('logs.db') as c:
        status = session["logged_in"]
        user = session["user_id"]
        create_date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
        if status is True:
            if request.method == 'POST':
                form_type = request.form.get('form_type')
                data_format = request.form.get('data_format')
                custom_filename = request.form.get('custom_filename')
                print("form type: {}".format(form_type))
                print("data format: {}".format(data_format))
                print("custom filename: {}".format(custom_filename))
                ################################################################################################################
                if form_type == "content-bar1":  # rentals
                    filter_data = {
                        'device_type': request.form.get('device-picker-bar1') if 'checkbox-bar1-1' in request.form else None,
                        'device_id': request.form.get('device-id-bar1') if 'checkbox-bar1-2' in request.form else None,
                        'start_date': request.form.get('date-picker-bar1-1') if 'checkbox-bar1-3' in request.form else None,
                        'end_date': request.form.get('date-picker-bar1-2') if 'checkbox-bar1-4' in request.form else None,
                        'exclude_overdues': 'exclude-overdues-bar1' in request.form,
                        'exclude_confirmed': 'exclude-confirmed-bar1' in request.form,
                        'exclude_unreturned': 'exclude-unreturned-bar1' in request.form,
                        'select_all_logs': 'select-all-bar1' in request.form
                    }
                    today = date.today()
                    formatted_date = today.strftime("%d-%m-%Y")
                    query = "SELECT * FROM device_logs WHERE 1=1"
                    params = []
                    print(filter_data)
                    filter_string = ""
                    if filter_data['device_type']:
                        query += " AND device_type = ?"
                        params.append(filter_data['device_type'])
                        filter_string += f"Device Type: {filter_data['device_type']}, "
                    if filter_data['device_id']:
                        query += " AND device_id = ?"
                        params.append(filter_data['device_id'])
                        filter_string += f"Device ID: {filter_data['device_id']}, "
                    if filter_data['start_date'] and filter_data['end_date']:
                        start_date = filter_data['start_date']
                        end_date = filter_data['end_date']
                        formatted_start = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d-%m-%Y")
                        formatted_end = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d-%m-%Y")
                        query += " AND date_borrowed >= ? AND date_borrowed <= ?"
                        params.append(formatted_start)
                        params.append(formatted_end)
                        filter_string += f"Start Date: {filter_data['start_date']}, "
                        filter_string += f"End Date: {filter_data['end_date']}, "
                    elif filter_data['start_date']:
                        start_date = filter_data['start_date']
                        formatted_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d-%m-%Y")
                        query += " AND SUBSTR(date_borrowed, 1, 10) = ?"
                        params.append(formatted_date)
                        filter_string += f"Start Date: {filter_data['start_Date']}, "
                    if filter_data['exclude_overdues']:
                        query += " AND SUBSTR(date_borrowed, 1, 10) != ? AND SUBSTR(date_borrowed, 1, 10) < ?"
                        params.append(formatted_date)
                        params.append(formatted_date)
                        filter_string += "Exclude Overdues, "
                    if filter_data['exclude_confirmed']:
                        query += " AND teacher_signoff != ?"
                        params.append("Confirmed")
                        filter_string += "Exclude Confirmed, "
                    if filter_data['exclude_unreturned']:
                        query += " AND period_returned != ?"
                        params.append('Not Returned')
                        filter_string += "Exclude Unreturned, "
                    if filter_data['select_all_logs']:
                        query = "SELECT * FROM device_logs"
                        params.clear()
                        filter_string += "Select All Logs"
                    #####################################################################################
                    rows = fetch_rows(c, query, params)
                    num_rows = len(rows)
                    constraints = filter_string
                    data_type = "Rental Logs"
                    file = "File Should Be Here"
                    rows = fetch_rows(c, query, params)
                    if data_format == "CSV":
                        if custom_filename:
                            filename = "{}.csv".format(custom_filename)
                        elif custom_filename is None:
                            filename = "device_logs.csv"

                        headers = ["Date Borrowed", "Submitted Under", "Student Name", "Homeroom", "Device Type",
                                   "Device ID", "Period Borrowed", "Reason Borrowed", "Period Returned",
                                   "Teacher Sign-Off", "Notes"]

                        generate_csv(filename, headers, rows)

                        response = make_response(send_file(filename, mimetype='text/csv', as_attachment=True))
                        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
                        c.execute("INSERT INTO download_logs (file_name, data_type, data_format, constraints, num_rows, created_by, created_date, file)VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (filename, data_type, data_format, constraints, num_rows, user, create_date, file))

                        return response

                    elif data_format == "PDF":
                        if custom_filename:
                            filename = "{}.pdf".format(custom_filename)
                        elif custom_filename is None:
                            filename = "device_logs.pdf"

                        headers = ["Date Borrowed", "Submitted Under", "Student Name", "Homeroom", "Device Type",
                                   "Device ID", "Period Borrowed", "Reason Borrowed", "Period Returned",
                                   "Confirmed", "Notes"]

                        # Generate the PDF file
                        generate_pdf(filename, headers, rows, constraints, user)

                        # Return the PDF file as a response
                        response = make_response(send_file(filename, mimetype='application/pdf', as_attachment=True))
                        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

                        # Insert the download_logs entry into the database
                        c.execute("INSERT INTO download_logs (file_name, data_type, data_format, constraints, num_rows, created_by, created_date, file)VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                  (filename, data_type, data_format, constraints, num_rows, user, create_date, file))

                        return response
                    

                ################################################################################################################    
                elif form_type == "content-bar2":  # devices
                    filter_data = {
                        'device_type': request.form.get('device-picker-bar2') if 'checkbox-bar2-1' in request.form else None,
                        'device_id': request.form.get('device-id-bar2') if 'checkbox-bar2-2' in request.form else None,
                        'start_date': request.form.get('date-picker-bar2-1') if 'checkbox-bar2-3' in request.form else None,
                        'end_date': request.form.get('date-picker-bar2-2') if 'checkbox-bar2-4' in request.form else None,
                        'exclude_in_circulation': 'in-circulation-bar2' in request.form,
                        'select_all': 'select-all-bar2' in request.form
                    }
                    formatted_date = date.today().strftime("%d-%m-%Y")
                    query = "SELECT device_id, device_type, date_added, last_change, added_by, in_circulation, notes, num_rentals, last_rental FROM devices WHERE 1=1"
                    params = []
                    filter_string = ""
                    if filter_data['device_type']:
                        query += " AND device_type = ?"
                        params.append(filter_data['device_type'])
                        filter_string += f"Device Type: {filter_data['device_type']}, "
                    if filter_data['device_id']:
                        query += " AND device_id = ?"
                        params.append(filter_data['device_id'])
                        filter_string += f"Device ID: {filter_data['device_id']}, "
                    if filter_data['start_date'] and filter_data['end_date']:
                        start_date = filter_data['start_date']
                        end_date = filter_data['end_date']
                        formatted_start = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d-%m-%Y")
                        formatted_end = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d-%m-%Y")
                        query += " AND last_rental >= ? AND last_rental <= ?"
                        params.append(formatted_start)
                        params.append(formatted_end)
                        filter_string += f"Start Date: {filter_data['start_date']}, "
                        filter_string += f"End Date: {filter_data['end_date']}, "
                    elif filter_data['start_date']:
                        start_date = filter_data['start_date']
                        formatted_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d-%m-%Y")
                        query += " AND SUBSTR(last_rental, 1, 10) = ?"
                        params.append(formatted_date)
                        filter_string += f"Start Date: {filter_data['start_date']}, "
                    if filter_data['exclude_in_circulation']:
                        query += " AND in_circulation != ?"
                        params.append("Yes")
                        filter_string += "Exclude In Circulation"
                    if filter_data['select_all']:
                        query = "SELECT * FROM devices"
                        params.clear()
                        filter_string += "Select All Devices"
                    #####################################################################3
                    rows = fetch_rows(c, query, params)
                    num_rows = len(rows)
                    constraints = filter_string
                    file = "File Should Be Here"
                    data_type = "Device Data"
                    if data_format == "CSV":
                        if custom_filename:
                            filename = "{}.csv".format(custom_filename)
                        elif custom_filename is None:
                            filename = "device_data.csv"

                        headers = ["Device ID", "Device Type", "Date Added", "Last Change", "Added By",
                                   "In Circulation", "Notes", "Num# Rentals",
                                   "Last Rental"]

                        generate_csv(filename, headers, rows)

                        response = make_response(send_file(filename, mimetype='text/csv', as_attachment=True))
                        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

                        c.execute("INSERT INTO download_logs (file_name, data_type, data_format, constraints, num_rows, created_by, created_date, file)VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (filename, data_type, data_format, constraints, num_rows, user, create_date, file))
                        return response
                    
                    elif data_format == "PDF":
                        if custom_filename:
                            filename = "{}.pdf".format(custom_filename)
                        elif custom_filename is None:
                            filename = "device_data.pdf"

                        headers = ["Device ID", "Device Type", "Date Added", "Last Change", "Added By",
                                   "In Circulation", "Notes","Barcode",  "Num# Rentals",
                                   "Last Rental"]

                         

                        # Generate the PDF file
                        generate_pdf_devices(filename, headers, rows, constraints, user)

                        # Return the PDF file as a response
                        response = make_response(send_file(filename, mimetype='application/pdf', as_attachment=True))
                        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

                        # Insert the download_logs entry into the database
                        c.execute("INSERT INTO download_logs (file_name, data_type, data_format, constraints, num_rows, created_by, created_date, file)VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                  (filename, data_type, data_format, constraints, num_rows, user, create_date, file))

                        return response
                ################################################################################################################
                elif form_type == "content-bar3":  # users
                    pass

            else:
                device_ids, device_types = get_device_list(c)
                return render_template('/download_logs.html', loginstatus=status, message="Download Data",
                                       device_ids=device_ids, device_types=device_types)
            device_ids, device_types = get_device_list(c)
            return render_template('/download_logs.html', loginstatus=status, message="Download Data",
                                   device_ids=device_ids, device_types=device_types)
        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",
                                   message_link="login-page")



def generate_csv(filename, headers, rows):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)

def fetch_rows(c, query, params):
    c.execute(query, params)
    return c.fetchall()


def generate_pdf(filename, headers, rows, constraints, user):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', '', 10)  

            header_width = self.w - 2 * self.l_margin
            header_height = 10

            if self.page_no() == 1:
                self.set_fill_color(255)  
                self.set_text_color(0) 
                self.set_font('Arial', '', 12)
                self.cell(header_width, header_height, filename, 0, 0, 'L', fill=True)
                self.set_x((self.w - self.get_string_width(f"Downloaded By: {user}")) / 2-110)  
                self.cell(0, header_height, f"Downloaded By: {user}", 0, 0, 'C') 
                self.cell(0, header_height, f"Date Downloaded: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}", 0, 0, 'R')  
                self.ln(header_height)  
            else:
                self.cell(header_width, header_height, "", 0, 0, 'L', fill=False)

            self.ln(5)





        def footer(self):
            # Set footer font and size
            self.set_font('Arial', 'I', 8)

            # Set footer text color to gray
            self.set_text_color(128)

            # Calculate footer width and height
            footer_width = self.w - 2 * self.l_margin
            footer_height = 10

            # Get current page number
            page_number = self.page_no()

            # Print footer
            self.cell(footer_width, footer_height, f"Page {page_number}", 0, 0, 'C')

        
        def table(self, headers, data):
            self.set_font('Arial', '', 8)  

            # Calculate page width (epw)
            page_width = self.w - 2 * self.l_margin
            num_columns = len(headers)
            column_width = page_width / num_columns
            column_widths = [column_width] * num_columns

            # Adjust column widths with custom widths
            column_widths[3] = column_width * 0.75
            column_widths[4] = column_width * 0.8
            column_widths[5] = column_width * 0.65
            column_widths[6] = column_width * 0.88
            column_widths[7] = column_width * 1.3
            column_widths[9] = column_width * 0.67
            column_widths[10] = column_width * 1.9

            self.set_fill_color(243)  
            self.set_text_color(0)  
            self.set_font('Arial', '', 10) 

            # Calculate row height
            row_height = self.font_size + 4

            # Print headers on the first page
            self.set_fill_color(0, 152, 121)  
            self.set_text_color(255)  
            self.set_font('Arial', 'B', 8)  

            for i, header in enumerate(headers):
                self.cell(column_widths[i], row_height, str(header), 1, 0, 'C', True)
            self.ln()

            row_number = 1

            for row in data:
                if self.y + row_height > self.page_break_trigger:
                    self.add_page()

                    # Print headers on new pages
                    self.set_fill_color(0, 152, 121) 
                    self.set_text_color(255)  
                    self.set_font('Arial', 'B', 8)  

                    for i, header in enumerate(headers):
                        self.cell(column_widths[i], row_height, str(header), 1, 0, 'C', True)
                    self.ln()

                if row_number % 2 == 0:
                    self.set_fill_color(255)  # Grey for even rows
                else:
                    self.set_fill_color(255, 255, 255)  # White for odd rows

                # Print row data
                self.set_fill_color(255) 
                self.set_text_color(0) 
                self.set_font('Arial', '', 8)  

                for i, column in enumerate(row):
                    self.cell(column_widths[i], row_height, str(column), 1, 0, 'L', fill=True)
                self.ln()

                row_number += 1

            self.ln(10)


    pdf = PDF(orientation='L')

    # Remove margin
    pdf.set_auto_page_break(auto=True, margin=0)
    pdf.l_margin = 0
    pdf.r_margin = 0
    pdf.t_margin = 0
    pdf.b_margin = 0

    #  table headers 
    pdf.add_page()

    if constraints:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Select Constraints:", 0, 1, 'L')
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(0, 10, constraints.strip(), 0, 'L')
        pdf.ln(10)

    # Generate the table
    pdf.table(headers, rows)

    # Save the PDF
    pdf.output(filename)

def generate_pdf_devices(filename, headers, rows, constraints, user):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', '', 10)

            header_width = self.w - 2 * self.l_margin
            header_height = 10

            if self.page_no() == 1:
                self.set_fill_color(255)
                self.set_text_color(0)
                self.set_font('Arial', '', 12)
                self.cell(header_width, header_height, filename, 0, 0, 'L', fill=True)
                self.set_x((self.w - self.get_string_width(f"Downloaded By: {user}")) / 2 - 110)
                self.cell(0, header_height, f"Downloaded By: {user}", 0, 0, 'C')
                self.cell(0, header_height, f"Date Downloaded: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}",
                          0, 0, 'R')
                self.ln(header_height)
            else:
                self.cell(header_width, header_height, "", 0, 0, 'L', fill=False)

            self.ln(5)

        def footer(self):
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128)
            footer_width = self.w - 2 * self.l_margin
            footer_height = 10
            page_number = self.page_no()
            self.cell(footer_width, footer_height, f"Page {page_number}", 0, 0, 'C')

        def table(self, headers, data):
            self.set_font('Arial', '', 8)
            page_width = self.w - 2 * self.l_margin
            num_columns = len(headers)
            column_width = page_width / num_columns
            column_widths = [column_width] * num_columns

            self.set_fill_color(243)
            self.set_text_color(0)
            self.set_font('Arial', '', 10)

            row_height = self.font_size + 4

            self.set_fill_color(0, 152, 121)
            self.set_text_color(255)
            self.set_font('Arial', 'B', 8)

            for i, header in enumerate(headers):
                self.cell(column_widths[i], row_height, str(header), 1, 0, 'C', True)
            self.ln()

            row_number = 1

            for row in data:
                if self.y + row_height > self.page_break_trigger:
                    self.add_page()
                    self.set_fill_color(0, 152, 121)
                    self.set_text_color(255)
                    self.set_font('Arial', 'B', 8)
                    for i, header in enumerate(headers):
                        self.cell(column_widths[i], row_height, str(header), 1, 0, 'C', True)
                    self.ln()

                if row_number % 2 == 0:
                    self.set_fill_color(255)
                else:
                    self.set_fill_color(255, 255, 255)

                self.set_fill_color(255)
                self.set_text_color(0)
                self.set_font('Arial', '', 8)

                for i, column in enumerate(row):
                    if i == 7: 
                        barcode_data = f"{row[1]}-{row[0]}"  

                        barcode_filename = f"{barcode_data}.png"
                        barcode_path = os.path.join("barcodes", barcode_filename)
                        if not os.path.exists(barcode_path):
                            barcode = Code128(barcode_data, writer=ImageWriter())
                            barcode.save(barcode_path)

                        if os.path.exists(barcode_path):
                            image_width = column_widths[i] - 2
                            image_height = row_height - 2
                            x = self.get_x()
                            y = self.get_y()
                            self.cell(column_widths[i], row_height, '', 1, 0, 'C', fill=True)
                            self.image(barcode_path, x + 1, y + 1, image_width, image_height)
                        else:
                            self.cell(column_widths[i], row_height, 'No barcode', 1, 0, 'C', fill=True)
                    else:
                        self.cell(column_widths[i], row_height, str(column), 1, 0, 'L', fill=True)
                self.ln()

                row_number += 1

            self.ln(10)

    pdf = PDF(orientation='L')
    pdf.set_auto_page_break(auto=True, margin=0)
    pdf.l_margin = 0
    pdf.r_margin = 0
    pdf.t_margin = 0
    pdf.b_margin = 0

    pdf.add_page()

    if constraints:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Select Constraints:", 0, 1, 'L')
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(0, 10, constraints.strip(), 0, 'L')
        pdf.ln(10)

    pdf.table(headers, rows)
    pdf.output(filename)




# page used to see previous downloads
@app.route('/previous-downloads/')
def prev_downloads():
    with opendb('logs.db') as c:
        status = session['logged_in']
        if status is True:
            return render_template('previous_downloads.html', loginstatus=status)
        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")



#page used to sign off circulations that have been returned
@app.route('/sign-off')
def sign_off():
    with opendb('logs.db') as c:
        status = session["logged_in"]
        if status is True:
        #selects all data from rental logs where data is unconfirmed
            c.execute("SELECT device_type, device_id, date_borrowed, submitted_under, student_name, homeroom, period_borrowed, reason_borrowed, period_returned, notes FROM device_logs WHERE teacher_signoff='Unconfirmed' AND period_returned IN ('Homeroom', 1, 2, 3, 4, 5, 6) AND period_returned != 'Not Returned'")
            rows = c.fetchall()
            return render_template('sign_off.html', rows=rows, loginstatus=status, message="Viewing unconfirmed circulations")
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
            return render_template('/device_modifier.html', loginstatus=status, rows=rows, message="Sign Off Device ID {}".format(device_id))
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

            return render_template('message.html', message=message, loginstatus=status, message_btn="View_Circulations", message_link="circulations")

        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login", message_link="login-page")


@app.route('/new-log')
@app.route('/new-log', methods=['POST'])
def new_log():
    # Open connection to the database
    with opendb('logs.db') as c:

        # Check if the user is logged in
        status = session["logged_in"]
        available_devices = c.execute("SELECT * FROM devices WHERE in_circulation = ?", ("No",))
    
        if request.method == "POST":
            form_type = request.form.get('form_type')
            device_type = request.form.get('device_type')
            # Retrieve form data
            formatted_date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")

            student_name = request.form.get('student_name')
            student_id = request.form.get('student_id')
            homeroom = request.form.get('homeroom')
            device_id = request.form.get('device_id')
            submitted_under = session['user_id']
            teacher_signoff = "Unconfirmed"
            current_date = date.today().strftime("%d-%m-%Y %H:%M")
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
                    (formatted_date, device_type, device_id, "Yes", student_name))
                else:
                    c.execute("INSERT INTO student_data(homeroom, student_name, num_rentals, last_rental, device_id, device_type, outstanding_rental, student_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                              (homeroom, student_name, 0, date, device_id, device_type, "Yes", student_id))
                c.execute("UPDATE student_data SET num_rentals = num_rentals + 1 WHERE student_name = ?", (student_name,))
                # Update devices table
                c.execute("UPDATE devices SET in_circulation = ?, last_rental = ? WHERE device_id = ? AND device_type = ?",
                ("Yes", formatted_date, device_id, device_type))
                # Update device logs table
                c.execute("INSERT INTO device_logs (date_borrowed, submitted_under, student_name, homeroom, device_type, device_id, period_borrowed, reason_borrowed, period_returned, teacher_signoff, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (formatted_date, submitted_under, student_name, homeroom, device_type, device_id, period_borrowed, reason_borrowed, "Not Returned", "Unconfirmed", notes))
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
            return render_template('new_log.html', loginstatus=status, available_devices=available_devices)


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
                    # Generate barcode image for device
                    randInt = random.randint(10000000, 99999999)
                    code128 = barcode.get_barcode_class('code128')
                    barcode_image = code128(str(device_type) + "-" + str(device_id) + "-" + str(randInt), writer=ImageWriter())
                    barcode_buffer = BytesIO()
                    barcode_image.write(barcode_buffer)
                    barcode_data = barcode_buffer.getvalue()
                    # Save barcode image to a file
                    barcode_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'barcodes')
                    os.makedirs(barcode_path, exist_ok=True)
                    barcode_file = os.path.join(barcode_path, f"{device_type}-{device_id}-{randInt}")
                    barcode_image.save(barcode_file)
                

                    # insert device data into database
                    c.execute("INSERT INTO devices (device_id, device_type, date_added,last_change, added_by, in_circulation, notes, barcode, num_rentals, last_rental) VALUES (?,?, ?, ?, ?, ?, ?, ?, ?, ?)", (device_id, device_type, date_submitted,"None",submitted_by, in_circulation, notes_device, barcode_data, 0, "None"))
                    return render_template('message.html', message="New device logged", loginstatus=status, message_btn="View_Devices",message_link="device-logs")
                elif device_exists_check:
                    return render_template('message.html', message="Device already exists", loginstatus=status, message_btn="Try_Again",message_link="new-item")   
                else:
                    return render_template('message.html', message="An unknown error occured. Please try again", loginstatus=status, message_btn="Try_Again",message_link="new-item") 
            else:
                return render_template('new_device.html', loginstatus=status)
        else:
            message = "Please login to access this feature"
            return render_template('message.html', message=message, loginstatus=status, message_btn="Login",message_link="login-page")
     
@app.route('/dev-admin', methods=['GET', 'POST'])
def dev_admin():
    pass


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
                                           loginstatus=status,  message_btn="Try_Again",message_link="signup-page")
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
                    return render_template('message.html', message="Sign Up success", loginstatus=status, message_btn="Login",message_link="login-page")
            else:
                return render_template('signup_page.html', loginstatus=status)

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
    loginstatus = session['logged_in']
    return render_template('help.html',loginstatus=loginstatus)
#Handles 400 errors -
@app.errorhandler(400)
def bad_request_error(error):
    status = session['logged_in']
    return render_template('error_page.html',error_code="400", error_message="Bad Request", loginstatus=status), 400
#Handles 401 errors - 
@app.errorhandler(401)
def unauthorized_error(error):
    status = session['logged_in']
    return render_template('error_page.html',error_code="401", error_message="Unauthorized", loginstatus=status), 401
#Handles 403 errors -
@app.errorhandler(403)
def forbidden_error(error):
    status = session['logged_in']
    return render_template('error_page.html',error_code="403", error_message="Forbidden", loginstatus=status), 403
#Handles 404 errors -
@app.errorhandler(404)
def page_not_found_error(error):
    status = session['logged_in']
    return render_template('error_page.html',error_code="404", error_message="Not Found", loginstatus=status), 404
#Handles 405 errors -
@app.errorhandler(405)
def method_not_allowed_error(error):
    status = session['logged_in']
    return render_template('error_page.html',error_code="405", error_message="Method Not Allowed", loginstatus=status), 405
#Handles 500 errors -
@app.errorhandler(500)
def internal_server_error(error):
    sql.session.rollback()
    status = session['logged_in']
    return render_template('error_page.html',error_code="500", error_message="Internal Server Error", loginstatus=status), 500
#Handles 503 errors -
@app.errorhandler(503)
def service_unavailable_error(error):
    status = session['logged_in']
    return render_template('error_page.html',error_code="503", error_message="Service Unavailable", loginstatus=status), 503



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



