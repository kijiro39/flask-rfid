from . import db
from flask_login import UserMixin
from sqlalchemy import ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())

## User Table
class User(db.Model, UserMixin):
    __tablename__ = "user"
    
    user_id = db.Column(db.String(10), primary_key=True)
    username = db.Column(db.String(50))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    user_type = db.Column(db.Integer)
    password = db.Column(db.String(100))
    date_added = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # Define a relationship with the Card model
    card_ref = db.relationship('Card', backref='user', uselist=False, cascade="all, delete-orphan")
    def get_id(self):
           return str(self.user_id)

## Card Table       
class Card(db.Model):
    __tablename__ = "card"
    
    card_id = db.Column(db.String(20), primary_key=True)
    uid = db.Column(db.String(10), db.ForeignKey('user.user_id'), unique=True)
    attendance_ref = db.relationship('Attendance', backref='attendance', uselist=False, cascade="all, delete-orphan")

## Attendance Table
class Attendance(db.Model):
    __tablename__ = "attendance"

    attendance_id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.String(20), db.ForeignKey('card.card_id'))
    clock_in = db.Column(db.DateTime(timezone=True))
    clock_out = db.Column(db.DateTime(timezone=True))

    # Define a relationship with the Card model
    card = db.relationship('Card', backref='attendance')
    
class Shift(db.Model):
    shift_id = db.Column(db.String, primary_key=True)
    time_in = db.Column(db.DateTime(timezone=True), default=func.now())
    time_out = db.Column(db.DateTime(timezone=True), default=func.now())

class Log(db.Model):
    log_id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer)
    activity = db.Column(db.String(255))
