from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, desc
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, time, timedelta
from . import db
import re

from .models import User, Card, Attendance

manager = Blueprint('manager', __name__)

def validate_password(password):
    # Password must have at least 1 uppercase letter, 1 lowercase letter, 1 symbol, and 1 number
    if not re.search(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", password):
        return False
    return True

def employee_count():
    employee_count = User.query.filter_by(user_type=3).count()
    return employee_count

@manager.route('/manager_home')
@login_required
def manager_home():
    count = employee_count()
    return render_template("manager.html", count=count, user=current_user)

@manager.route('/manager_edit', methods=['GET', 'POST'])
@login_required
def manager_edit():
    
    data = User.query.get(current_user.user_id)
    db.session.commit()
    
    return render_template("edit_profile.html", user=current_user, data=data)

@manager.route('/manager_edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        
        upd_username = request.form.get('username')
        upd_first_name = request.form.get('first_name')
        upd_last_name = request.form.get('last_name')
        upd_password = request.form.get('password')
        upd_confirm_password = request.form.get('confirm_password')
        
        data = User.query.filter_by(user_id=current_user.user_id).first()
        
        if upd_password == upd_confirm_password:
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
            return redirect(url_for('manager.manager_home', user=current_user))
        else:
            flash('Process error!', category='error')
    else:
        flash('Process error!', category='error')
    
    return render_template("edit_profile.html", user=current_user)

@manager.route('/view_emp', methods=['GET', 'POST'])
@login_required
def display_employee():
    
    list = User.query.filter(User.user_type == 3).order_by(desc(User.date_added)).all()
    
    return render_template("emp_list.html", list=list, user=current_user)

@manager.route('/view_emp_profile/<string:id>', methods=['POST'])
@login_required
def view_emp_profile(id):
    
    employee = User.query.get(id)
    card_id = db.session.query(Card.card_id).filter(Card.uid == id).scalar()
    db.session.commit()
    
    return render_template("view_emp_profile.html", user=current_user, employee=employee, card_id=card_id)

@manager.route('/search_emp')
def search():
    term = request.args.get('term', '')
    users = User.query.filter(or_(User.user_id.ilike(f'%{term}%'), User.username.ilike(f'%{term}%'), User.first_name.ilike(f'%{term}%'), User.last_name.ilike(f'%{term}%'), User.card_ref.has(Card.card_id.ilike(f'%{term}%')))).all()
    return render_template('emp_list_partial.html', list=users, user=current_user)

@manager.route('/manager_viewrec')
@login_required
def manager_viewrec():
    attendance_data = []

    # Retrieve the attendance records and associated user information
    attendance_records = Attendance.query.join(Card).join(User).order_by(desc(Attendance.clock_in)).all()

    # Extract the required information from the records
    for record in attendance_records:
        clock_in_time = record.clock_in
        clock_out_time = record.clock_out
        
        # Call the define_status function to determine the initial status
        status = define_status(clock_in_time, clock_out_time)
        
        attendance_data.append({
            'date': record.clock_in.strftime('(%A)%d-%m-%Y'),
            'user_id': record.card.user.user_id,
            'first_name': record.card.user.first_name,
            'last_name': record.card.user.last_name,
            'card_id': record.card.card_id,
            'status': status
        })
        
    # Check for suspicious attendance records
    suspicious_records = find_suspicious_records(attendance_records)

    # Update the status for suspicious records
    for record in suspicious_records:
        attendance_data[record['index']]['status'] = 'Suspicious'

    # Pass the attendance data to the template
    return render_template('manager_viewrec.html', attendance_data=attendance_data, user=current_user)

def define_status(clock_in, clock_out):
    status = ''
    start_shift = time(18, 0)
    end_shift = time(23, 0)
    end_scan = time(23, 30)
    
    if clock_in and clock_out:
        clock_in = clock_in.time()
        clock_out = clock_out.time()
        if clock_in > start_shift and clock_out >= end_scan:
            status = 'Absent'
        elif clock_in > start_shift and clock_out < end_scan:
            status = 'Late'
        elif clock_in < start_shift and clock_out < end_shift:
            status = 'Excuse'
        else:
            status = 'Present'
    elif clock_in and not clock_out:
        status = 'Working'
    return status

def find_suspicious_records(attendance_records):
    suspicious_records = []
    counter = 0  # Counter to keep track of repeated occurrences
    
    for i in range(len(attendance_records)):
        for j in range(i+1, len(attendance_records)):
            if attendance_records[i].card.card_id != attendance_records[j].card.card_id:
                time_diff = abs(attendance_records[i].clock_in - attendance_records[j].clock_in)
                if time_diff < timedelta(milliseconds=6000):
                    counter += 1
                    if counter == 3:
                        suspicious_records.append({'index': j})  # Set 'Suspicious' status on the third occurrence
                else:
                    counter = 0
    
    return suspicious_records
    
def set_suspicious_status(attendance_list):
    count = 0

    for i in range(1, len(attendance_list)):
        current_attendance = attendance_list[i]
        previous_attendance = attendance_list[i - 1]

        time_diff = (current_attendance.clock_in - previous_attendance.clock_in).total_seconds()

        if time_diff <= 6:
            count += 1
            if count == 3:
                return True
        else:
            count = 0

    return False