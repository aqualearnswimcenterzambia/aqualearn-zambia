from flask_sqlalchemy import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default='client')  # 'client', 'coach', 'manager'
    total_sessions = db.Column(db.Integer, default=10)
    remaining_sessions = db.Column(db.Integer, default=10)
    package_name = db.Column(db.String(100), default='Basic')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_marked = db.Column(db.String(100), nullable=False)

class CoachLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_name = db.Column(db.String(150), nullable=False)
    session_time = db.Column(db.String(100), nullable=False)
    date_logged = db.Column(db.String(100), nullable=False)
    amount_expected = db.Column(db.Float, default=0.0)