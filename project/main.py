from website import create_app
import pymysql
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, time
                  
app = create_app()

@app.route("/")
def default_landing_page():
    if request.host == "127.0.0.1:5000":
        return redirect(url_for('auth.scan_attendance'))
    else:
        return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True)