from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from project.extensions import db
from project.models import User
from project.services.navigation import redirect_dashboard
from project.services.security import check_password, hash_password

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_dashboard(current_user.role)
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password(password, user.password):
            login_user(user)
            return redirect_dashboard(user.role)
        flash('Invalid email or password')
    return render_template('login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect_dashboard(current_user.role)
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        district = request.form.get('district')
        panchayat = request.form.get('panchayat')
        ward_number = request.form.get('ward_number')

        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('auth.register'))

        user = User(
            name=name,
            email=email,
            phone=phone,
            password=hash_password(password),
            role='Citizen',
            district=district,
            panchayat=panchayat,
            ward_number=int(ward_number) if ward_number else None,
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('dashboards.citizen_dashboard'))
    return render_template('register.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
