# python -m flask run

from flask import Flask, render_template
app = Flask(__name__, static_url_path='/static')



# Home page
@app.route('/')
def main():
    return render_template('/index.html')

@app.route('/device-logs')
def index():
    return render_template('device_logs.html')

#Handles 403 errors -
@app.errorhandler(403)
def forbidden_error(error):
    return render_template('error_page.html'), 403

#Handles 404 errors -
@app.errorhandler(404)
def page_not_found_error(error):
    return render_template('error_page.html'), 404

if __name__ == '__main__':
    app.run(debug="True")