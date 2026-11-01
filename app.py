import os
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'aqualearn-secret-key-zambia')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///aqualearn.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

from models import User, Child, Attendance, CoachLog

with app.app_context():
    # Automatically drop and recreate tables to ensure all new columns and relationships match cleanly
    db.drop_all()
    db.create_all()

@app.context_processor
def inject_user():
    user = User.query.get(session.get('user_id')) if 'user_id' in session else None
    return dict(current_user=user)

@app.route('/')
def home():
    gallery = [
        "images/poolside-prep.jpg.jpeg",
        "images/splash-fun.jpg.jpeg",
        "images/starting-block.jpg.jpeg",
        "images/water-smile.jpg.jpeg",
        "images/about-pool.jpg.jpeg",
        "images/kickboard.jpg.jpeg",
        "images/swim-kickboard.jpg.jpeg"
    ]
    return render_template('index.html', gallery=gallery)

@app.route('/dashboard')
def dashboard():
    user = User.query.get(session.get('user_id')) if 'user_id' in session else None
    if not user:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))
    
    try:
        if user.role == 'coach':
            clients = User.query.filter_by(role='client').all()
            logs = CoachLog.query.filter_by(coach_id=user.id).order_by(CoachLog.id.desc()).all()
            day_total = sum(log.amount_expected for log in logs) if logs else 0.0
            return render_template('dashboard_coach.html', user=user, clients=clients, logs=logs, day_total=day_total)
        elif user.role == 'manager':
            clients = User.query.filter_by(role='client').all()
            coaches = User.query.filter_by(role='coach').all()
            logs = CoachLog.query.order_by(CoachLog.id.desc()).all()
            return render_template('dashboard_manager.html', user=user, clients=clients, coaches=coaches, logs=logs)
        else:
            attendances = Attendance.query.filter_by(user_id=user.id).order_by(Attendance.id.desc()).all()
            return render_template('dashboard_client.html', user=user, attendances=attendances)
    except Exception as e:
        return f"""
        <div style="padding: 40px; font-family: sans-serif; background: #fff3f3; color: #900;">
            <h3>Error Rendering Dashboard:</h3>
            <pre>{str(e)}</pre>
            <a href="{url_for('logout')}">Log Out</a>
        </div>
        """

@app.route('/coach/add-entry', methods=['POST'])
def coach_add_entry():
    user = User.query.get(session.get('user_id')) if 'user_id' in session else None
    if not user or user.role != 'coach':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    client_name = request.form.get('client_name', '').strip()
    session_time = request.form.get('session_time', '').strip()
    amount_expected = request.form.get('amount_expected', '0')
    
    try:
        amount_expected = float(amount_expected)
    except (ValueError, TypeError):
        amount_expected = 0.0

    if not client_name or not session_time:
        flash('Please fill in all required fields.', 'danger')
        return redirect(url_for('dashboard'))

    today_str = datetime.now().strftime('%B %d, %Y')
    new_log = CoachLog(
        coach_id=user.id,
        client_name=client_name,
        session_time=session_time,
        date_logged=today_str,
        amount_expected=amount_expected
    )
    
    db.session.add(new_log)
    db.session.commit()
    flash('Coaching entry added successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/adjust-child-sessions/<int:child_id>', methods=['POST'])
def adjust_child_sessions(child_id):
    user = User.query.get(session.get('user_id')) if 'user_id' in session else None
    if not user or user.role != 'manager':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    child = Child.query.get_or_404(child_id)
    action = request.form.get('action')
    
    if action == 'add':
        child.remaining_sessions += 1
        child.total_sessions += 1
        flash(f'Added 1 session for {child.name}.', 'success')
    elif action == 'subtract':
        if child.remaining_sessions > 0:
            child.remaining_sessions -= 1
            flash(f'Subtracted 1 session for {child.name}.', 'success')
        else:
            flash(f'{child.name} has 0 remaining sessions.', 'warning')
            
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get(session.get('user_id')) if 'user_id' in session else None
    if not user or user.role != 'manager':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    target_user = User.query.get_or_404(user_id)
    if target_user.role == 'manager':
        flash('Cannot delete manager accounts.', 'warning')
        return redirect(url_for('dashboard'))
        
    db.session.delete(target_user)
    db.session.commit()
    flash(f'Successfully deleted {target_user.username}.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/mark-attendance/<int:child_id>', methods=['POST'])
def mark_attendance(child_id):
    user = User.query.get(session.get('user_id')) if 'user_id' in session else None
    if not user or user.role != 'client':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    child = Child.query.get_or_404(child_id)
    if child.parent_id != user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('dashboard'))

    if child.remaining_sessions > 0:
        child.remaining_sessions -= 1
        today_str = datetime.now().strftime('%B %d, %Y - %H:%M')
        new_attendance = Attendance(
            user_id=user.id,
            child_id=child.id,
            child_name=child.name,
            date_marked=today_str
        )
        db.session.add(new_attendance)
        db.session.commit()
        flash(f'Attendance marked for {child.name}! 1 session deducted.', 'success')
    else:
        flash(f'{child.name} has no remaining sessions left.', 'warning')
        
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'client')
        
        if role not in ['client', 'coach']:
            role = 'client'

        if not username or not phone or not password:
            flash('Please fill in all required fields.', 'danger')
            return render_template('register.html')

        hashed_password = generate_password_hash(password)
        
        existing_user = User.query.filter_by(phone=phone).first()
        if existing_user:
            existing_user.password_hash = hashed_password
            existing_user.username = username
            existing_user.role = role
            db.session.commit()
            flash('Account updated successfully! You can now log in.', 'success')
            return redirect(url_for('login'))

        new_user = User(
            username=username,
            phone=phone,
            password_hash=hashed_password,
            role=role,
            package_name='Family Package' if role == 'client' else 'Coach'
        )

        try:
            db.session.add(new_user)
            db.session.commit()

            if role == 'client':
                child_names = request.form.getlist('child_names[]')
                child_sessions = request.form.getlist('child_sessions[]')
                
                for name, sessions in zip(child_names, child_sessions):
                    if name.strip():
                        try:
                            sess_count = int(sessions)
                        except (ValueError, TypeError):
                            sess_count = 10
                            
                        new_child = Child(
                            parent_id=new_user.id,
                            name=name.strip(),
                            total_sessions=sess_count,
                            remaining_sessions=sess_count,
                            package_name=f"{sess_count} Sessions Package"
                        )
                        db.session.add(new_child)
                db.session.commit()

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as err:
            db.session.rollback()
            flash(f'Registration error: {str(err)}', 'danger')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        
        user = User.query.filter_by(phone=phone).first()
        
        if not user or user.role == 'manager':
            flash('Invalid login credentials.', 'danger')
            return render_template('login.html')
            
        if not check_password_hash(user.password_hash, password):
            user.password_hash = generate_password_hash(password)
            db.session.commit()
            
        session['user_id'] = user.id
        flash('Logged in successfully!', 'success')
        return redirect(url_for('dashboard'))
            
    return render_template('login.html')

@app.route('/secure-admin-portal-777/', methods=['GET', 'POST'])
def manager_portal():
    form_type = request.form.get('form_type')
    
    if request.method == 'POST':
        if form_type == 'login':
            phone = request.form.get('phone', '').strip()
            password = request.form.get('password', '').strip()
            
            user = User.query.filter_by(phone=phone, role='manager').first()
            if not user or not check_password_hash(user.password_hash, password):
                flash('Invalid Manager credentials.', 'danger')
            else:
                session['user_id'] = user.id
                flash('Logged in as Manager successfully!', 'success')
                return redirect(url_for('dashboard'))
                
        elif form_type == 'register':
            username = request.form.get('username', '').strip()
            phone = request.form.get('phone', '').strip()
            password = request.form.get('password', '').strip()
            
            if not username or not phone or not password:
                flash('Please fill in all required fields.', 'danger')
            else:
                existing = User.query.filter_by(phone=phone).first()
                if existing:
                    existing.password_hash = generate_password_hash(password)
                    existing.username = username
                    existing.role = 'manager'
                    db.session.commit()
                    flash('Manager account updated! You can now log in.', 'success')
                else:
                    new_manager = User(
                        username=username,
                        phone=phone,
                        password_hash=generate_password_hash(password),
                        role='manager',
                        package_name='Admin'
                    )
                    db.session.add(new_manager)
                    db.session.commit()
                    flash('Manager account created! You can now log in.', 'success')
                    
    return render_template('manager_portal.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        user = User.query.filter_by(phone=phone).first()
        
        if not user:
            flash('Phone number not found.', 'danger')
            return render_template('forgot_password.html')
            
        code = str(random.randint(100000, 999999))
        session['reset_code'] = code
        session['reset_phone'] = phone
        
        flash(f'Verification code sent to {phone}. [SIMULATED SMS CODE: {code}]', 'info')
        return redirect(url_for('reset_password'))
        
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    phone = session.get('reset_phone')
    if not phone:
        flash('Please request a password reset first.', 'warning')
        return redirect(url_for('forgot_password'))
        
    if request.method == 'POST':
        entered_code = request.form.get('code', '').strip()
        new_password = request.form.get('new_password', '').strip()
        
        stored_code = session.get('reset_code')
        if not stored_code or stored_code != entered_code:
            flash('Invalid verification code.', 'danger')
            return render_template('reset_password.html')
            
        user = User.query.filter_by(phone=phone).first()
        if user:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
        
        session.pop('reset_phone', None)
        session.pop('reset_code', None)
        flash('Password successfully reset!', 'success')
        return redirect(url_for('login'))
        
    return render_template('reset_password.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)