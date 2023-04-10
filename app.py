# python -m flask run

from flask import Flask, render_template, url_for, redirect
app = Flask(__name__, static_url_path='/static')



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
@app.route('/signup-page')
def signup_page():
    return render_template('/signup_page.html')


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
    db.session.rollback()
    return render_template('error_page.html'), 500

#Handles 503 errors -
@app.errorhandler(503)
def service_unavailable_error(error):
    return render_template('error_page.html'), 503




# Responsible for running the website
if __name__ == '__main__':
    app.run(debug="True")