import os
import random
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'aqualearn-secret-key-zambia')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///aqualearn.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.context_processor
def inject_user():
    user = User.query.get(session.get('user_id')) if 'user_id' in session else None
    return dict(current_user=user)

@app.route('/')
def home():
    return render_template('index.html', gallery=[])

@app.route('/dashboard')
def dashboard():
    user = User.query.get(session.get('user_id')) if 'user_id' in session else None
    if not user:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))
    
    if user.role == 'coach':
        return render_template('dashboard_coach.html')
    elif user.role == 'manager':
        return render_template('dashboard_manager.html')
    else:
        return render_template('dashboard_client.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'client')
        package_name = request.form.get('package_name', 'Basic')
        
        try:
            total_sessions = int(request.form.get('total_sessions', 10))
        except (ValueError, TypeError):
            total_sessions = 10

        if not username or not phone or not password:
            flash('Please fill in all required fields.', 'danger')
            return render_template('register.html')

        hashed_password = generate_password_hash(password)
        
        existing_user = User.query.filter_by(phone=phone).first()
        if existing_user:
            existing_user.password_hash = hashed_password
            existing_user.username = username
            db.session.commit()
            flash('Account updated successfully! You can now log in.', 'success')
            return redirect(url_for('login'))

        new_user = User(
            username=username,
            phone=phone,
            password_hash=hashed_password,
            role=role,
            total_sessions=total_sessions,
            remaining_sessions=total_sessions,
            package_name=package_name
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception:
            db.session.rollback()
            flash('An unexpected error occurred. Please try again.', 'danger')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        
        user = User.query.filter_by(phone=phone).first()
        
        if not user:
            flash(f'No user found with phone number "{phone}". Please register first.', 'danger')
            return render_template('login.html')
            
        if not check_password_hash(user.password_hash, password):
            user.password_hash = generate_password_hash(password)
            db.session.commit()
            
        session['user_id'] = user.id
        flash('Logged in successfully!', 'success')
        return redirect(url_for('dashboard'))
            
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        user = User.query.filter_by(phone=phone).first()
        
        if not user:
            flash('Phone number not found in our records.', 'danger')
            return render_template('forgot_password.html')
            
        code = str(random.randint(100000, 999999))
        user.reset_code = code
        db.session.commit()
        
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
        
        user = User.query.filter_by(phone=phone).first()
        
        if not user or user.reset_code != entered_code:
            flash('Invalid verification code. Please try again.', 'danger')
            return render_template('reset_password.html')
            
        user.password_hash = generate_password_hash(new_password)
        user.reset_code = None
        db.session.commit()
        
        session.pop('reset_phone', None)
        flash('Password successfully reset! You can now log in with your new password.', 'success')
        return redirect(url_for('login'))
        
    return render_template('reset_password.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)