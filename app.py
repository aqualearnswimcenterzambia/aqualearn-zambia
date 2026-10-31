from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid
from models import db, User, GalleryItem, Attendance, CoachLog

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aqualearn-secret-key-zambia'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aqualearn.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def seed_gallery():
    if GalleryItem.query.count() == 0:
        photos = [
            GalleryItem(title="Splash Fun", filename="splash-fun.jpg.jpeg", col_size="col-md-4"),
            GalleryItem(title="Starting Block", filename="starting-block.jpg.jpeg", col_size="col-md-4"),
            GalleryItem(title="Kickboard Drill", filename="kickboard.jpg.jpeg", col_size="col-md-4"),
            GalleryItem(title="Happy Swimmer", filename="water-smile.jpg.jpeg", col_size="col-md-6"),
            GalleryItem(title="Poolside Confidence", filename="swim-kickboard.jpg.jpeg", col_size="col-md-6"),
            GalleryItem(title="Poolside Prep", filename="poolside-prep.jpg.jpeg", col_size="col-md-12"),
        ]
        db.session.bulk_save_objects(photos)
        db.session.commit()

with app.app_context():
    db.create_all()
    seed_gallery()

@app.route('/')
def home():
    gallery_images = GalleryItem.query.all()
    return render_template('index.html', gallery=gallery_images)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role = request.form.get('role', 'client').lower().strip()
        package = request.form.get('package', '10')

        if User.query.filter_by(username=username).first():
            flash('Username is already taken.', 'danger')
            return redirect(url_for('register'))

        sessions = int(package) if role == 'client' else 0
        hashed = generate_password_hash(password)

        new_user = User(
            username=username, 
            phone=phone, 
            password_hash=hashed, 
            role=role,
            total_sessions=sessions,
            remaining_sessions=sessions,
            package_name=f"{sessions} Sessions Package" if role == 'client' else 'Staff'
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Route users strictly based on their database role
    if current_user.role == 'coach':
        return redirect(url_for('coach_portal'))
    elif current_user.role == 'manager':
        return redirect(url_for('manager_portal'))
    else:
        return redirect(url_for('client_portal'))

@app.route('/dashboard/client')
@login_required
def client_portal():
    if current_user.role != 'client':
        flash('Access denied. This portal is for clients only.', 'danger')
        return redirect(url_for('dashboard'))
    
    my_attendances = Attendance.query.filter_by(client_id=current_user.id).order_by(Attendance.id.desc()).all()
    return render_template('dashboard_client.html', attendances=my_attendances)

@app.route('/dashboard/coach')
@login_required
def coach_portal():
    if current_user.role != 'coach':
        flash('Access denied. This portal is for coaches only.', 'danger')
        return redirect(url_for('dashboard'))

    today = datetime.now().strftime("%Y-%m-%d")
    # Strictly isolate logs so each coach sees only their own entries
    logs = CoachLog.query.filter_by(coach_id=current_user.id, date_logged=today).all()
    day_total = sum(log.amount_expected for log in logs)
    clients = User.query.filter_by(role='client').all()
    return render_template('dashboard_coach.html', logs=logs, day_total=day_total, clients=clients)

@app.route('/dashboard/manager')
@login_required
def manager_portal():
    if current_user.role != 'manager':
        flash('Access denied. This portal is for managers only.', 'danger')
        return redirect(url_for('dashboard'))

    clients = User.query.filter_by(role='client').all()
    coaches = User.query.filter_by(role='coach').all()
    all_coach_logs = CoachLog.query.order_by(CoachLog.id.desc()).all()
    attendances = Attendance.query.order_by(Attendance.id.desc()).all()
    return render_template('dashboard_manager.html', clients=clients, coaches=coaches, logs=all_coach_logs, attendances=attendances)

# CLIENT ACTION: Mark Attendance & Subtract Session
@app.route('/client/mark-attendance', methods=['POST'])
@login_required
def mark_attendance():
    if current_user.role != 'client':
        abort(403)
    if current_user.remaining_sessions > 0:
        current_user.remaining_sessions -= 1
        today = datetime.now().strftime("%Y-%m-%d %H:%M")
        att = Attendance(client_id=current_user.id, date_marked=today, status='Logged')
        db.session.add(att)
        db.session.commit()
        flash('Attendance marked! Remaining sessions reduced by 1.', 'success')
    else:
        flash('You have 0 remaining sessions! Please renew your package.', 'danger')
    return redirect(url_for('client_portal'))

# COACH ACTION: Add Client Coaching Log & Auto Count Total
@app.route('/coach/add-entry', methods=['POST'])
@login_required
def coach_add_entry():
    if current_user.role != 'coach':
        abort(403)
    client_name = request.form.get('client_name')
    session_time = request.form.get('session_time')
    amount = float(request.form.get('amount_expected', 0))
    today = datetime.now().strftime("%Y-%m-%d")

    log = CoachLog(
        coach_id=current_user.id,
        client_name=client_name,
        session_time=session_time,
        amount_expected=amount,
        date_logged=today,
        submission_group=str(uuid.uuid4())
    )
    db.session.add(log)
    db.session.commit()
    flash(f'Coaching log added for {client_name} (K{amount}).', 'success')
    return redirect(url_for('coach_portal'))

# MANAGER ACTION: Adjust Sessions Manually
@app.route('/manager/adjust-sessions/<int:user_id>', methods=['POST'])
@login_required
def adjust_sessions(user_id):
    if current_user.role != 'manager':
        abort(403)
    client = User.query.get_or_404(user_id)
    action = request.form.get('action')
    if action == 'add':
        client.remaining_sessions += 1
    elif action == 'subtract' and client.remaining_sessions > 0:
        client.remaining_sessions -= 1
    db.session.commit()
    flash(f"Updated {client.username}'s remaining sessions to {client.remaining_sessions}.", 'info')
    return redirect(url_for('manager_portal'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)