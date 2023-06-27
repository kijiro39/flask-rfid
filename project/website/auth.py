from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, Card, Attendance
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime, time
from sqlalchemy import desc

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    logout_user()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user)
                if user.user_type == 1:
                    return redirect(url_for('admin.admin_home'))
                elif user.user_type == 2:
                    return redirect(url_for('manager.manager_home'))
                elif user.user_type == 3:
                    return redirect(url_for('employee.employee_home'))
                    
            else:
                flash('Incorrect password. Please try again.', category='error')
        else:
            flash('Username does not exist.', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/scan_attendance', methods=['GET', 'POST'])
def scan_attendance():
    logout_user()
    
    if request.method == 'POST':
        card_id = request.form.get('card_id')
        
        action = check_clock_action(card_id)
        user = User.query.join(Card).filter(Card.card_id == card_id).first()

        if user:
            current_time = datetime.now()

            if action == "clock_in":
                attendance = Attendance(card_id=card_id, clock_in=current_time)
            else:
                attendance = Attendance.query.filter_by(card_id=card_id).order_by(desc(Attendance.attendance_id)).first()
                attendance.clock_out = current_time

            db.session.add(attendance)
            db.session.commit()

            flash("Attendance recorded successfully", "success")
            return render_template("display_scan.html", user=user, attendance=attendance)
        else:
            flash("Invalid card ID", "error")

        return redirect(url_for('auth.scan_attendance'))
    
    return render_template("scan_attendance.html", user=current_user)

def check_clock_action(card_id):
    latest_attendance = Attendance.query.filter_by(card_id=card_id).order_by(desc(Attendance.attendance_id)).first()
    
    if latest_attendance:
        if latest_attendance.clock_in is not None and latest_attendance.clock_out is None:
            return"clock_out"
        elif latest_attendance.clock_in is not None and latest_attendance.clock_out is not None:
            return"clock_in"
    
    return "clock_in"

def check_attendance():
    # Get the current date and time
    current_date = datetime.now().date()
    current_time = datetime.now().time()

    # Check if it's a working day (excluding Friday)
    if current_date.weekday() != 4:  # Assuming Monday is 0 and Sunday is 6
        # Get the shift start and end times
        shift_start_time = datetime.combine(current_date, time(18, 0))
        shift_end_time = datetime.combine(current_date, time(23, 0))

        # Get the employees who started working the previous day
        employees = User.query.join(Card).filter(User.user_type == 3, Card.card_id.isnot(None)).all()

        for employee in employees:
            # Check if the employee's shift has ended
            if current_time >= shift_end_time.time():
                # Check if the employee has already scanned their attendance
                attendance = Attendance.query.filter_by(user_id=employee.user_id, date=current_date).first()
                if not attendance:
                    # Set the attendance status as 'Absent' if not scanned
                    attendance = Attendance(user_id=employee.user_id, 
                                            clock_in=current_time,
                                            clock_out=current_time
                                            )
                    db.session.add(attendance)
                    db.session.commit()