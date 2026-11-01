from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='client')
    package_name = db.Column(db.String(50), default='Basic')
    total_sessions = db.Column(db.Integer, default=10)
    remaining_sessions = db.Column(db.Integer, default=10)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_marked = db.Column(db.String(50), nullable=False)

class CoachLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_name = db.Column(db.String(100), nullable=False)
    session_time = db.Column(db.String(100), nullable=False)
    date_logged = db.Column(db.String(50), nullable=False)
    amount_expected = db.Column(db.Float, nullable=False)

    coach = db.relationship('User', backref=db.backref('logs', lazy=True))