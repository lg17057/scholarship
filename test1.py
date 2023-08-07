#here is my code i've updated it to work for creating a session if a user has logged in
# but im confused on how to make each users session different depending on their log in  


#i have added logic that i think might work for your code. I am unsure as i cant run your code at the moment, try it and let me know. 

import sqlite3
from sqlite3 import *
import bcrypt
from bottle import route, run, debug, view, template, request, static_file, error,redirect,response
from datetime import datetime

 



def create_todo_table(name):
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    table_name = f"{name}_todo"
    c.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY, task TEXT, status INTEGER)")
    conn.commit()
    c.close()



def check_existing_user(name):
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute("SELECT name FROM users WHERE name = ?", (name,))
    result = c.fetchone()
    conn.commit()
    c.close()
    if result is not None:
        return True
    else:
        return False


def create_new_user(name, password,):
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    table_name = f"{name}_todo"
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    with sqlite3.connect('todo.db') as conn:
        c = conn.cursor()

        c.execute("INSERT INTO users (name, password) VALUES (?, ?)", (name, hashed_password))
        

        conn.commit()

    create_todo_table(name)


@route('/sign_up', method='GET')
def signup():
    return  template('sign_up')


@route('/sign_up', method='POST')
def go_sign_up():
    name = request.forms.get('name')
    password = request.forms.get('password')

    if check_existing_user(name):
        return template('failed_page.tpl', name=name), "<p class='head'>Name already exists. Please choose a different name.</p>"
    else:
        response.set_cookie("userloginstatus", value='True' )
        #i am adding this user id cookie because i am assuming that once a user creates an account they are logged in to that account immediately
        response.set_cookie("user_id", value=name)
        

        create_todo_table(name)  
        create_new_user(name, password)
        return redirect('/home/' + name)
        


def check_login(name,password):
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE name = ?", (name,))
    result = c.fetchone()
    c.close()
    if result is not None:
        hashed_password = result[0]
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
            return True

    return False



@route('/login', method='GET')
def login():
    
    return template('login')


@route('/login', method='POST')
def go_login():
   
    name = request.forms.get('name')
    password = request.forms.get('password')

    if check_login(name, password):
        response.set_cookie("userloginstatus", value='True' )
        #setting user id cookie to the value of the name
        #only set if login is succesful
        response.set_cookie("user_id", value=name)

        redirect('/home/' + name)
    else:
        #set loginstatus to false if check_login returns 'false'
        response.set_cookie("userloginstatus", value='False' )
        #set current user id to 'none' as no user is logged in
        response.set_cookie("user_id", value='none')

        return template('failed_page.tpl', name=name), "<p class='head' >Login failed.</p>"



@route('/home/<name>')
def home(name):
    current_user = request.get_cookie("userloginstatus")
    if current_user == 'False':
        redirect('/login')
    else:
        
        conn = sqlite3.connect('todo.db')
        c = conn.cursor()
        #setting variable equal to the value of the cookie
        current_user_id = request.get_cookie("user_id")
        #checks if the name that was used for the redirect is equal to the current user id cookie value
        if name == current_user_id:
            return template('home_page', name=name)
        else:
            redirect('/login')
        c.close()
    


@route('/todo/<name>')
def display_info(name):
    current_user = request.get_cookie("userloginstatus")
    if current_user == 'False':
        redirect('/login')
    else:
        #setting variable equal to the value of the cookie
        current_user_id = request.get_cookie("user_id")
        #checks if the name that was used for the redirect is equal to the current user id cookie value
        if  name == current_user_id:
            conn = sqlite3.connect('todo.db')
            c = conn.cursor()
            table_name = f"{name}_todo"
            c.execute(f"SELECT id, task FROM {table_name} WHERE status LIKE '1'")
            result = c.fetchall()
            c.close()
            output = template('make_table.tpl', name=name, rows=result)
            return output
        else:
            return 'You cannot access this page as you are not logged in with the valid username'
            #redirect to other page
            #could redirect to login page or could redirect to page telling them that they are not logged in with that username
            #add this logic to what other pages you might want
        


@route('/new/<name>', method='GET')
def new_item(name):
    current_user = request.get_cookie("userloginstatus")
    if current_user == 'False':
        redirect('/login')
    else:
        current_user_id = request.get_cookie("user_id")
        #same check to see if name matches user id cookie
        if name == current_user_id:
            if request.GET.save:
                new = request.GET.task.strip()
                table_name = f"{name}_todo"
                conn = sqlite3.connect('todo.db')
                c = conn.cursor()
                c.execute(f"INSERT INTO {table_name} (task, status) VALUES (?, ?)", (new, 1))
                new_id = c.lastrowid
                conn.commit()
                c.close()
                return template('back_home', name=name), '<h1>The new task was inserted into the database, the ID is %s</h1>' % new_id
            else:
                return template('new_task.tpl', name=name)
        else:
            return 'You cannot access this page as you are not logged in with the valid username'
            #redirect to other page
            #could redirect to login page or could redirect to page telling them that they are not logged in with that username
