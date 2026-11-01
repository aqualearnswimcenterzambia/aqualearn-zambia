from extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default='client')
    package_name = db.Column(db.String(100), default='Family Package')
    
    children = db.relationship('Child', backref='parent', cascade='all, delete-orphan', lazy=True)

class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    package_name = db.Column(db.String(100), default='Standard Package')
    total_sessions = db.Column(db.Integer, default=10)
    remaining_sessions = db.Column(db.Integer, default=10)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=True)
    child_name = db.Column(db.String(150), nullable=True)
    date_marked = db.Column(db.String(100), nullable=False)

class CoachLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_name = db.Column(db.String(150), nullable=False)
    session_time = db.Column(db.String(100), nullable=False)
    date_logged = db.Column(db.String(100), nullable=False)
    amount_expected = db.Column(db.Float, default=0.0)