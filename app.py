from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from app import app, db, User  # Adjust import names to match your project structure

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role = request.form.get('role', 'client')  # Default to client
        package_name = request.form.get('package_name', 'Basic')
        total_sessions = int(request.form.get('total_sessions', 10))

        # Check if basic required fields are filled
        if not username or not phone or not password:
            flash('Please fill in all required fields.', 'danger')
            return render_template('register.html')

        # Hash password securely
        hashed_password = generate_password_hash(password)

        # Create new user object
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
            db.session.rollback()  # Clear the failed database transaction
            flash('A user with that phone number or username already exists.', 'danger')
            return render_template('register.html')

        except Exception as e:
            db.session.rollback()
            flash('An unexpected error occurred. Please try again.', 'danger')
            return render_template('register.html')

    return render_template('register.html')