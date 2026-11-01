import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from models import db, User

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'aqualearn-secret-key-zambia')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///aqualearn.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Ensure database tables are created within application context
with app.app_context():
    db.create_all()

# Context processor so 'current_user' is always available in templates
@app.context_processor
def inject_user():
    user = User.query.get(session.get('user_id')) if 'user_id' in session else None
    return dict(current_user=user)

@app.route('/')
def home():
    gallery_items = []
    return render_template('index.html', gallery=gallery_items)

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
        username = request.form.get('username')
        phone = request.form.get('phone')
        password = request.form.get('password')
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
        except IntegrityError:
            db.session.rollback()
            flash('That phone number or username is already registered.', 'danger')
            return render_template('register.html')
        except Exception as e:
            db.session.rollback()
            flash('An unexpected error occurred. Please try again.', 'danger')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Accept phone, username, or identifier input from the form
        identifier = request.form.get('phone') or request.form.get('username') or request.form.get('identifier')
        password = request.form.get('password')
        
        # Check against both phone and username columns in the database
        user = User.query.filter((User.phone == identifier) | (User.username == identifier)).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid phone number or password.', 'danger')
            return render_template('login.html')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)