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
def index_data(c, formatted_date, yesterday, dates):
    c.execute("SELECT date_borrowed FROM device_logs WHERE SUBSTR(date_borrowed, 1,10) = ?", (formatted_date,))
    rows = c.fetchall()
    row_1 = len(rows)
    #total rentals today
    c.execute("SELECT date_borrowed FROM device_logs WHERE SUBSTR(date_borrowed, 1,10) = ? AND period_returned != 'Not Returned'", (formatted_date,))
    rows = c.fetchall()
    row_2 = len(rows)
    #devices returned today
    c.execute("SELECT date_borrowed FROM device_logs WHERE SUBSTR(date_borrowed, 1,10) = ? AND teacher_signoff = 'Confirmed'", (formatted_date,))
    rows = c.fetchall()
    row_3 = len(rows)
    c.execute("SELECT date_borrowed, device_type, device_id, student_name, homeroom, period_borrowed FROM device_logs WHERE date_borrowed <= ? AND teacher_signoff != ? AND SUBSTR(date_borrowed,1,5) != ?", (yesterday, "Confirmed", dates))
    rows = c.fetchall()
    row_4 = len(rows)
    c.execute("SELECT date_borrowed, device_type, device_id, student_name, homeroom, period_borrowed FROM device_logs WHERE date_borrowed <= ? AND teacher_signoff != ? AND SUBSTR(date_borrowed,1,5) != ?", (yesterday, "Confirmed", dates))
    rows = c.fetchall()
    
    #selects all devices that are overdue (takes all values from date_borrowed value of formatted_yesterday and earlier)
    c.execute("SELECT date_borrowed, device_type, device_id, student_name, homeroom, period_borrowed FROM device_logs WHERE SUBSTR(date_borrowed, 1,10) = ? AND period_returned = ? AND teacher_signoff = ?", (formatted_date,"Not Returned","Unconfirmed"))
    row1 = c.fetchall()

    return row_1,row_2,row_3,row_4, rows, row1
def homeroom_data(c):
    year_levels = ['7', '8', '9', '10', '11', '12', '13']

    homeroom_codes = {}
    for year_level in year_levels:
        if year_level == '10' or year_level == '11' or year_level == '12' or year_level == '13':
            c.execute("SELECT SUBSTR(code, 3, 5) FROM homerooms WHERE SUBSTR(code, 1, 2) = ?", (year_level,))
        elif year_level == '7' or year_level == '8' or year_level == '9':
            c.execute("SELECT SUBSTR(code, 2, 5) FROM homerooms WHERE SUBSTR(code, 1, 1) = ?", (year_level,))
        codes = [code[0] for code in c.fetchall()]
        homeroom_codes[f'year{year_level}_codes'] = codes
    return codes, homeroom_codes, year_levels
def date_data():
    today = date.today()
    formatted_date = today.strftime("%d-%m-%Y")
    dates = datetime.datetime.now().date().strftime("%d-%m-%yyyy")
    yesterday = date.today() - timedelta(days=1)
    formatted_yesterday = yesterday.strftime("%d-%m-%Y")
    return today, formatted_date, dates, yesterday, formatted_yesterday
def device_available(device_type, c):
    query = "SELECT * FROM devices WHERE device_type = ? AND in_circulation = 'No'"
    c.execute(query)
    result = c.fetchall()
    if result:
        deviceavailable = "Yes"
    else:
        deviceavailable = "No"
    return deviceavailable
def student_exists(student_name, student_id, c):
    query = "SELECT * FROM devices WHERE student_name = ? AND student_id = ?"
    c.execute(query)
    result = c.fetchone()
    if result:
        studentexists = "Yes"
    else:
        studentexists = "No"
    return studentexists
def student_exists_scan(student_name, student_id, c):
    query = "SELECT * FROM devices WHERE student_name = ? AND student_id = ?",(student_name,student_id)
    c.execute(query)
    result = c.fetchone()
    if result:
        studentexists_scan = "Yes"
    else:
        studentexists_scan = "No"
    return studentexists_scan
def rental_exists(device_id,device_type,c):
    query = "SELECT * FROM device_logs WHERE device_id = ? AND device_type = ? AND teacher_signoff = ? AND period_returned = ?",(device_id, device_type, "Unconfirmed", "Not Returned")
    c.execute(query)
    result = c.fetchall()
    rentalexists = ""
    if result is None:
        rentalexists == "No"
    elif result is not None:
        rentalexists == "Yes"
    return rentalexists
def device_exists(device_type,device_id, c):
    query = "SELECT * FROM devices WHERE device_type = ? and device_id = ?",(device_type,device_id)
    c.execute(query)
    deviceexists = c.fetchall()
    if deviceexists is None: 
        deviceexists = "Yes"
    elif deviceexists is not None:
        deviceexists = "No"
    return deviceexists
def form_type_rent():
    period_borrowed = request.form.get('period_borrowed')
    reason_borrowed = request.form.get('reason_borrowed')
    notes = request.form.get('notes') or "No notes"
    return period_borrowed,reason_borrowed, notes
def form_type_return():
    period_returned = request.form.get('period_returned')
    notes = request.form.get('notes') or "No notes"
    return period_returned, notes
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



@app.route('/')
@app.route('/', methods=['GET','POST'])
def main():
    session.setdefault('logged_in', False)
    session.setdefault('user_id', "Invalid")
    with opendb('logs.db') as c:
        status = session['logged_in']
        if status is True:
            if request.method == "POST":
                form_type = request.form.get('form_type')
                device_type = request.form.get('device_type')
                device_id = request.form.get('device_id')
                student_name = request.form.get('student_name')
                student_id = request.form.get('student_id')
                homeroom = request.form.get('year_level') + request.form.get('code_select')
                submitted_under = session['user_id']
                teacher_signoff = "Unconfirmed"
                current_date = date.today().strftime("%d-%m-%Y %H:%M")
                ############################################################################
                if device_type and device_id is None:
                    barcode_input = request.form.get('barcode_input')
                    device_type, device_id = barcode_input.split('-')
                if student_id is None:
                    student_id = request.form.get('id_input')

                
                deviceavailable = device_available(device_type, c)
                if deviceavailable == "Yes":
                    pass
                elif deviceavailable == "No":
                    return render_template('/message.html')

                deviceexists = device_exists(device_type,device_id, c)
                if deviceexists == "Yes":
                    pass
                elif deviceexists == "No":
                    return render_template('/message.html')

                studentexists = student_exists(student_name,student_id, c)
                studentexists_scan = student_exists_scan(student_name,student_id,c)
                if form_type == "rent":
                    period_borrowed,reason_borrowed, notes = form_type_rent()
                    if studentexists == "Yes":
                        c.execute("UPDATE student_data SET last_rental = ?, device_type = ?, device_id = ?, outstanding_rental = ?, num_rentals = num_rentals + 1 WHERE student_name = ? AND student_id = ?",(current_date, device_type, device_id, "Yes", student_name, student_id))
                    elif studentexists == "No":
                        c.execute("INSERT INTO student_data(homeroom, student_name, num_rentals, last_rental, device_id, device_type, outstanding_rental, student_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",(homeroom, student_name, 1, date, device_id, device_type, "Yes", student_id))
                    c.execute("UPDATE devices SET in_circulation = ?, last_rental = ?, num_rentals = num_rentals + 1 WHERE device_id = ? AND device_type = ?",("Yes", current_date, device_id, device_type))
                    c.execute("INSERT INTO device_logs (date_borrowed, submitted_under, student_name, homeroom, device_type, device_id, period_borrowed, reason_borrowed, period_returned, teacher_signoff, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",(current_date, submitted_under, student_name, homeroom, device_type, device_id, period_borrowed, reason_borrowed, "Not Returned", "Unconfirmed", notes))
                    return render_template('message.html', message="Successful Rental", loginstatus=status, message_btn="View_Rental_Logs", message_link="rental-logs")
                elif form_type == "rent_scan":
                    period_borrowed,reason_borrowed, notes = form_type_rent()
                    
                    if studentexists_scan == "Yes":
                        c.execute("UPDATE student_data SET last_rental = ?, device_type = ?, device_id = ?, outstanding_rental = ?, num_rentals = num_rentals + 1 WHERE student_name = ? AND student_id = ?",(current_date, device_type, device_id, "Yes", student_name, student_id))
                    elif studentexists_scan == "No":
                        c.execute("INSERT INTO student_data(homeroom, student_name, num_rentals, last_rental, device_id, device_type, outstanding_rental, student_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",(homeroom, student_name, 1, date, device_id, device_type, "Yes", student_id))
                    c.execute("UPDATE devices SET in_circulation = ?, last_rental = ?, num_rentals = num_rentals + 1 WHERE device_id = ? AND device_type = ?",("Yes", current_date, device_id, device_type))
                    c.execute("INSERT INTO device_logs (date_borrowed, submitted_under, student_name, homeroom, device_type, device_id, period_borrowed, reason_borrowed, period_returned, teacher_signoff, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",(current_date, submitted_under, student_name, homeroom, device_type, device_id, period_borrowed, reason_borrowed, "Not Returned", "Unconfirmed", notes))
                    return render_template('message.html', message="Successful Rental", loginstatus=status, message_btn="View_Rental_Logs", message_link="rental-logs")
                elif form_type == "return":
                    period_returned, notes = form_type_return()
                    rentalexists = rental_exists(device_id,device_type,c)
                    if rentalexists == "No":
                        return render_template('/message.html')
                    elif rentalexists == "Yes":
                        pass
                    if studentexists == "Yes":
                        c.execute("UPDATE student_data SET last_rental = ?, device_type = ?, device_id = ?, outstanding_rental = ? WHERE student_name = ?",(current_date, device_type, device_id, "No", student_name))
                    elif studentexists == "No":
                        return render_template('message.html', message="Student has no outstanding rentals", loginstatus=status, message_btn="Return_Device", message_link="new-log")
                    c.execute("UPDATE devices SET in_circulation = ? WHERE device_id = ? AND device_type = ?",("No", device_id, device_type,))
                    c.execute("UPDATE device_logs SET period_returned = ?, notes = ? WHERE device_id = ? AND device_type = ?",(period_returned, notes, device_id, device_type))
                    return render_template('message.html', message="Device Returned", loginstatus=status, message_btn="View_Rental_Logs", message_link="rental-logs")
                elif form_type == "return_scan":
                    period_return, notes = form_type_return()
                    rentalexists = rental_exists(device_id,device_type,c)
                    if rentalexists == "No":
                        return render_template('/message.html')
                    elif rentalexists == "Yes":
                        pass
                    if studentexists == "Yes":
                        c.execute("UPDATE student_data SET last_rental = ?, device_type = ?, device_id = ?, outstanding_rental = ? WHERE student_name = ?",(current_date, device_type, device_id, "No", student_name))
                    elif studentexists == "No":
                        return render_template('message.html', message="Student has no outstanding rentals", loginstatus=status, message_btn="Return_Device", message_link="new-log")
                    c.execute("UPDATE devices SET in_circulation = ? WHERE device_id = ? AND device_type = ?",("No", device_id, device_type,))
                    c.execute("UPDATE device_logs SET period_returned = ?, notes = ? WHERE device_id = ? AND device_type = ?",(period_returned, notes, device_id, device_type))
                    return render_template('message.html', message="Device Returned", loginstatus=status, message_btn="View_Rental_Logs", message_link="rental-logs")
            else:
                codes , homeroom_codes,year_levels = homeroom_data(c)
                today, formatted_date, dates, yesterday, formatted_date = date_data()
                row_1,row_2,row_3,row_4, rows, row1 = index_data(c, formatted_date, yesterday, dates)
                device_ids, device_types = get_device_list(c)
                return render_template('/index.html', row1_descriptor=row_1, row2_descriptor=row_2, row3_descriptor=row_3, row4_descriptor=row_4, message="Index Page", loginstatus=status, rows=rows, row1=row1, device_ids=device_ids, device_types=device_types, codes=codes,homeroom_codes=homeroom_codes)
        else:
            #person not logged in goes here
            session['logged_in'] = False
            session['user_id'] = "Invalid"
            device_ids, device_types = get_device_list(c)
            return render_template('/index.html', message="Index Page. Please login to access data", loginstatus=status, device_ids=device_ids, device_types=device_types)