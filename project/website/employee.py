from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, desc
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
import re
from datetime import datetime, time
from .models import User, Card, Attendance

employee = Blueprint('employee', __name__)

def validate_password(password):
    # Password must have at least 1 uppercase letter, 1 lowercase letter, 1 symbol, and 1 number
    if not re.search(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", password):
        return False
    return True

@employee.route('/employee_home')
@login_required
def employee_home():
    return render_template("employee.html", user=current_user)

@employee.route('/employee_edit', methods=['GET', 'POST'])
@login_required
def manager_edit():
    
    data = User.query.get(current_user.user_id)
    db.session.commit()
    
    return render_template("edit_profile.html", user=current_user, data=data)

@employee.route('/employee_edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        
        upd_username = request.form.get('username')
        upd_first_name = request.form.get('first_name')
        upd_last_name = request.form.get('last_name')
        upd_password = request.form.get('password')
        upd_confirm_password = request.form.get('confirm_password')
        
        data = User.query.filter_by(user_id=current_user.user_id).first()
        
        if User.query.filter_by(username=upd_username).first() and upd_username != data.username:
            flash('Username already taken. Try another.', category='error')
            return render_template("edit_profile.html", user=current_user, data=data)
        elif upd_password == upd_confirm_password:
            valid_password = validate_password(upd_password)
            if valid_password is False:
                flash('Password must have least 8 characters, consists of at least 1 uppercase letter, 1 lowercase letter, 1 symbol, and 1 number', category="error")
                return render_template("edit_profile.html", user=current_user, data=data)        
            
            data.username = upd_username
            data.first_name = upd_first_name
            data.last_name = upd_last_name
            data.password = generate_password_hash(upd_password, method='sha256')
        
            db.session.commit()
            flash('Edit successful!', category='success')
            return redirect(url_for('employee.employee_home', user=current_user))
        else:
            flash('Process error!', category='error')
    else:
        flash('Process error!', category='error')
    
    return render_template("edit_profile.html", user=current_user)

@employee.route('/employee_viewrec')
@login_required
def emp_viewrec():
    attendance_data = []

    # Retrieve the attendance records and associated user information based on the card_id
    attendance_records = Attendance.query.join(Card, Card.card_id == Attendance.card_id).join(User, User.user_id == Card.uid).filter(User.user_id == current_user.user_id).order_by(desc(Attendance.clock_in)).all()
    card_id = db.session.query(Card.card_id).filter(Card.uid == current_user.user_id).scalar()
    # Extract the required information from the records
    for record in attendance_records:
        clock_in_time = record.clock_in
        clock_out_time = record.clock_out
        status = define_status(clock_in_time, clock_out_time)
        attendance_data.append({
            'date': record.clock_in.strftime('(%A)%d-%m-%Y'),
            'clock_in': clock_in_time,
            'clock_out': clock_out_time,
            'status': status
        })

    # Pass the attendance data to the template
    return render_template('employee_viewrec.html', attendance_data=attendance_data, user=current_user, card_id=card_id)

def define_status(clock_in, clock_out):
    status = ''
    start_shift = time(18, 0)
    end_shift = time(23, 0)
    
    if clock_in and clock_out:
        clock_in = clock_in.time()
        clock_out = clock_out.time()
        if clock_in > start_shift and clock_out > end_shift:
            status = 'Absent'
        elif clock_in > start_shift and clock_out < end_shift:
            status = 'Late'
        else:
            status = 'Present'
    elif clock_in and not clock_out:
        status = 'Working'
    return status