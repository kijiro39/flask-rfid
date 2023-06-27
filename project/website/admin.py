from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, func, desc
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, time, timedelta, date
from . import db
import re
import random
import string

from .models import User, Card, Attendance

admin = Blueprint('admin', __name__)

def validate_password(password):
    # Password must have at least 1 uppercase letter, 1 lowercase letter, 1 symbol, and 1 number
    if not re.search(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", password):
        return False
    return True

def validate_user_id(user_id):
    pattern = r'^[A-Z0-9]{1,10}$'
    return re.match(pattern, user_id) is not None

def generate_user_id():
    letters = string.ascii_uppercase
    digits = string.digits

    # Generate the first 2 characters as uppercase alphabets
    first_part = ''.join(random.choice(letters) for _ in range(2))

    # Generate the ninth character as an uppercase alphabet
    ninth_character = random.choice(letters)

    # Generate the remaining 6 characters as numbers
    second_part = ''.join(random.choice(digits) for _ in range(6))
    
    # Generate the last character as number
    last_character = random.choice(digits)

    user_id = f"{first_part}{second_part}{ninth_character}{last_character}"
    return user_id

def user_count():
    count = User.query.count()
    return count

@admin.route('/admin_home')
@login_required
def admin_home():
    count = user_count()
    return render_template("admin.html", count=count, user=current_user)

@admin.route('/admin_edit', methods=['GET', 'POST'])
@login_required
def admin_edit():
    
    data = User.query.get(current_user.user_id)
    db.session.commit()
    
    return render_template("edit_profile.html", user=current_user, data=data)

@admin.route('/admin_edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        
        upd_username = request.form.get('username')
        upd_first_name = request.form.get('first_name')
        upd_last_name = request.form.get('last_name')
        upd_password = request.form.get('password')
        upd_confirm_password = request.form.get('confirm_password')
        
        data = User.query.filter_by(user_id=current_user.user_id).first()
        
        if User.query.filter_by(username=upd_username).first():
            flash('Username already taken. Try another.', category='error')
            return render_template("edit_profile.html", user=current_user, data=data)
        elif upd_password == upd_confirm_password:
            valid_password = validate_password(upd_password)
            if valid_password is False:
                flash('Password must have at least 8 characters, consists of at least 1 uppercase letter, 1 lowercase letter, 1 symbol, and 1 number', category="error")
                return render_template("edit_profile.html", user=current_user, data=data)
            
            data.username = upd_username
            data.first_name = upd_first_name
            data.last_name = upd_last_name
            data.password = generate_password_hash(upd_password, method='sha256')
        
            db.session.commit()
            flash('Edit successful!', category='success')
            return redirect(url_for('admin.admin_home', user=current_user))
        else:
            flash('Password doesn\'t match', category='error')
            return render_template("edit_profile.html", user=current_user, data=data)
    else:
        flash('Process error!', category='error')
    
    return render_template("edit_profile.html", user=current_user)

@admin.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        user_type = request.form.get('user_type')
        password = request.form.get('password')
        card_id = request.form.get('card_id') if user_type == '3' else None
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already taken. Try another.', category='error')
        elif len(username) < 4:
            flash('Username must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif len(last_name) < 2:
            flash('Last name must be greater than 1 character.', category='error')
        elif len(password) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            user_id=generate_user_id()
            if validate_user_id(user_id) is True:
                valid_id = user_id
            new_user = User(user_id=valid_id,
                            username=username,
                            first_name=first_name, 
                            last_name=last_name, 
                            user_type=user_type, 
                            password=generate_password_hash(password, method='sha256'),
                            )
            db.session.add(new_user)
            db.session.commit()
            if user_type == '3' and card_id:
                existing_card = Card.query.filter_by(card_id=card_id).first()
                if existing_card:
                    flash('The Card ID already existed. Please enter a different Card ID.', category='error')
                new_card = Card(card_id=card_id, uid=new_user.user_id)
                db.session.add(new_card)
                db.session.commit()
                     
            flash('New user added.', category='success')
            return redirect(url_for('admin.add_user'))

    return render_template("add_user.html", user=current_user)

@admin.route('/view_user', methods=['GET', 'POST'])
@login_required
def display_user():
    users = User.query.filter(User.user_type.in_([2, 3])).order_by(desc(User.date_added)).all()
    
    for user in users:
        if user.date_added:
            date_added = str(user.date_added)
            user.date_added = datetime.strptime(date_added, "%Y-%m-%d").strftime("%d-%m-%Y")
    
    return render_template("user_list.html", list=users, user=current_user)

@admin.route('/search_user')
def search():
    term = request.args.get('term', '')
    users = User.query.filter(or_(User.user_id.ilike(f'%{term}%'), User.username.ilike(f'%{term}%'), User.first_name.ilike(f'%{term}%'), User.last_name.ilike(f'%{term}%'))).all()
    return render_template('user_list_partial.html', list=users)

@admin.route('/update_user/<string:id>', methods=['GET', 'POST'])
@login_required
def view_user(id):
    
    data = User.query.get(id)
    card_id = db.session.query(Card.card_id).filter(Card.uid == id).scalar()
    db.session.commit()
    
    return render_template("update_user.html", user=current_user, data=data, card_id=card_id)

@admin.route('/update/<string:id>', methods=['GET', 'POST'])
@login_required
def update_user(id):
    if request.method == 'POST':
        
        upd_username = request.form.get('username')
        upd_first_name = request.form.get('first_name')
        upd_last_name = request.form.get('last_name')
        upd_user_type = request.form.get('current_user_type')
        upd_password = request.form.get('password')
        
        data = User.query.filter_by(user_id=id).first()
           
        data.username = upd_username
        data.first_name = upd_first_name
        data.last_name = upd_last_name
        data.password = generate_password_hash(upd_password, method='sha256')
        
        if upd_user_type == '3':  # If user type is employee
            current_card_id = db.session.query(Card.card_id).filter(Card.uid == id).scalar()
            upd_card_id = request.form.get('card_id')
            existing_card = Card.query.filter(Card.uid != id, Card.card_id == upd_card_id).first()
            if not upd_card_id:
                flash('Please enter the Card ID.', category='error')
                return render_template('update_user.html', user=current_user, id=id, data=data, card_id=current_card_id)
            if existing_card:
                flash('The Card ID is already associated with another user. Please enter a different card ID.', category='error')
                return render_template('update_user.html', user=current_user, id=id, data=data, card_id=current_card_id)
            else:
                card = Card.query.filter_by(uid=id).first()
                if card:
                    card.card_id = upd_card_id
                else:
                    new_card = Card(card_id=upd_card_id, uid=id)
                    db.session.add(new_card)

        db.session.commit()
        flash('User update successful!', category='success')
        return redirect(url_for('admin.display_user', user=current_user))
    else:
        flash('Process error!', category='error')
    
    return render_template("update_user.html", user=current_user)

@admin.route('/delete/<string:id>', methods=['POST'])
@login_required
def erase(id): 
    # deletes the data on the basis of unique id and
    # directs to home page
    data = User.query.get(id)
    db.session.delete(data)
    db.session.commit()
    
    flash('User successfully deleted!', category='success')
    return redirect(url_for('admin.display_user'))

@admin.route('/example')
def example_route():
    host = request.host
    return f"The host being used is: {host}"

# Admin view attendance record
@admin.route('/admin_viewrec')
@login_required
def admin_viewrec():
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
            'clock_in': clock_in_time.strftime('%H:%M:%S'),
            'clock_out': clock_out_time.strftime('%H:%M:%S'),
            'status': status
        })
        
    # Check for suspicious attendance records
    suspicious_records = find_suspicious_records(attendance_records)

    # Update the status for suspicious records
    for record in suspicious_records:
        attendance_data[record['index']]['status'] = 'Suspicious'

    # Pass the attendance data to the template
    return render_template('admin_viewrec.html', attendance_data=attendance_data, user=current_user)

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

def find_suspicious_records(attendance_records):
    suspicious_records = []
    counter = 0  # Counter to keep track of repeated occurrences
    
    for i in range(len(attendance_records)):
        for j in range(i+1, len(attendance_records)):
            if attendance_records[i].card.card_id != attendance_records[j].card.card_id:
                time_diff = abs(attendance_records[i].clock_in - attendance_records[j].clock_in)
                if time_diff < timedelta(seconds=60):
                    counter += 1
                    if counter == 3:
                        suspicious_records.append({'index': j})  # Set 'Suspicious' status on the third occurrence
                else:
                    counter = 0
    
    return suspicious_records

@admin.route('/update_record', methods=['POST'])
def check_attendance():
    current_date = date.today()  # Current date
    current_time = datetime.now().time()  # Current time

    # Create a new datetime object with the current date and time
    current_datetime = datetime.combine(current_date, current_time)
    # Check if it's a working day (excluding Friday)
    if current_date.weekday() != 4:  # Assuming Monday is 0 and Sunday is 6
        # Get the shift start and end times
        
        shift_start_time = datetime.combine(current_date, time(18, 0))
        shift_end_time = datetime.combine(current_date, time(23, 0))
        
        #     if current_time >= shift_end_time.time():
        #         # Check if the employee has already scanned their attendance
        #         attendance = Attendance.query.filter(user_id=employee.user_id, clock_in=current_date).first()
        #         if not attendance:
        #             # Set the attendance status as 'Absent' if not scanned
        #             attendance = Attendance(user_id=employee.user_id, 
        #                                     clock_in=current_time,
        #                                     clock_out=current_time
        #                                     )
        #             db.session.add(attendance)
        #             db.session.commit()
        #             return render_template('admin_viewrec.html', user=current_user, attendance_data=attendance)
        missing_card_ids = find_missing_attendance(current_date)
        if missing_card_ids:
            # Print the missing card IDs
            for card_id in missing_card_ids:
                attendance = Attendance(card_id=card_id,
                                        clock_in=current_datetime,
                                        clock_out=current_datetime
                                        )
                db.session.add(attendance)
                db.session.commit()
            
        return redirect(url_for('admin.admin_viewrec'))
             
    return render_template('admin_viewrec.html', user=current_user)

def find_missing_attendance(current_date):
    start_datetime = datetime.combine(current_date, datetime.min.time())
    end_datetime = start_datetime + timedelta(days=1) - timedelta(seconds=1)
    
    # Retrieve all card IDs
    card_ids = [card.card_id for card in Card.query.all()]

    # Filter the card IDs that don't have an attendance record within the current day
    missing_card_ids = [card_id for card_id in card_ids if not Attendance.query.filter(Attendance.card_id == card_id, 
                                                                                       Attendance.clock_in >= start_datetime, 
                                                                                       Attendance.clock_in <= end_datetime
                                                                                       ).first()]
    return missing_card_ids