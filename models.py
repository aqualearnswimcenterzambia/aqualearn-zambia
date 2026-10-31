from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='client')  # 'client', 'coach', 'manager'
    
    # Client Specific Fields
    total_sessions = db.Column(db.Integer, default=0)
    remaining_sessions = db.Column(db.Integer, default=0)
    package_name = db.Column(db.String(100), default='')
    
    # Relationships
    attendances = db.relationship('Attendance', backref='client', lazy=True, foreign_keys='Attendance.client_id')
    coach_logs = db.relationship('CoachLog', backref='coach', lazy=True, foreign_keys='CoachLog.coach_id')

class GalleryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    col_size = db.Column(db.String(20), default='col-md-4')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_marked = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Logged')

class CoachLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_name = db.Column(db.String(80), nullable=False)
    session_time = db.Column(db.String(50), nullable=False)
    amount_expected = db.Column(db.Float, nullable=False)
    date_logged = db.Column(db.String(50), nullable=False)
    submission_group = db.Column(db.String(100), nullable=False)