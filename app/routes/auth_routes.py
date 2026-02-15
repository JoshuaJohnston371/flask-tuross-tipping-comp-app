from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user
from ..models import User
from .. import db

auth_bp = Blueprint('auth', __name__)

# Register route (disabled)
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please use a different Username.', 'danger')
            return redirect(url_for('auth.register'))

        new_user = User(name=name, username=username)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()

        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', request_method=request.method)

# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Login failed. Check your username and password.', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('login.html')