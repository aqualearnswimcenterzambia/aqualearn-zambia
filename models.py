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
    reset_code = db.Column(db.String(6), nullable=True) # Added for password reset