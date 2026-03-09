import os
import uuid

import bcrypt
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from models import Complaint, User, db
from app.config import CONFIG_BY_NAME, DevelopmentConfig, ProductionConfig

login_manager = LoginManager()

ALLOWED_STATUSES = {'Submitted', 'In Progress', 'Resolved'}
ROLE_STATUS_TRANSITIONS = {
    'Ward Member': {
        'Submitted': {'In Progress'},
        'In Progress': {'Resolved'},
        'Resolved': set(),
    },
    'Department Officer': {
        'Submitted': {'In Progress'},
        'In Progress': {'Resolved'},
        'Resolved': set(),
    },
    'President': {
        'Submitted': {'Resolved'},
        'In Progress': {'Resolved'},
        'Resolved': set(),
    },
    'Admin': {
        'Submitted': {'In Progress', 'Resolved'},
        'In Progress': {'Resolved'},
        'Resolved': set(),
    },
}
DEPARTMENT_NAME_MAPPING = {
    'Sanitation': 'Sanitation Department',
    'Electricity': 'Electricity Department',
    'Public Works': 'Public Works Department',
    'Water Supply': 'Water Supply Department',
}


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def is_department_officer_authorized(user, complaint):
    if user.role != 'Department Officer':
        return False

    user_department = (user.department or '').strip()
    complaint_department = (complaint.department or '').strip()
    mapped_department = DEPARTMENT_NAME_MAPPING.get(user_department, user_department)
    return complaint_department in {user_department, mapped_department}


def can_user_update_complaint(user, complaint):
    if user.role == 'Citizen':
        return False
    if user.role == 'Ward Member':
        return complaint.ward_number == user.ward_number
    if user.role == 'Department Officer':
        return is_department_officer_authorized(user, complaint)
    if user.role in {'President', 'Admin'}:
        return True
    return False


def get_status_options_for_complaint(user, complaint):
    if not can_user_update_complaint(user, complaint):
        return []

    role_transitions = ROLE_STATUS_TRANSITIONS.get(user.role, {})
    return sorted(role_transitions.get(complaint.status, set()))


def classify_department_and_priority(text):
    text = text.lower()
    department = 'General'
    priority = 'Low'
    if 'street light' in text or 'electricity' in text or 'streetlight' in text:
        department = 'Electricity Department'
        priority = 'Medium'
    elif 'garbage' in text or 'sanitation' in text or 'waste' in text:
        department = 'Sanitation Department'
        priority = 'High'
    elif 'road' in text or 'pothole' in text or 'damage' in text:
        department = 'Public Works Department'
        priority = 'Medium'
    elif 'water' in text or 'leak' in text or 'drainage' in text or 'pipe' in text:
        department = 'Water Supply Department'
        priority = 'High'

    if 'danger' in text or 'accident' in text or 'urgent' in text or 'safety' in text:
        priority = 'High'

    return department, priority


def redirect_dashboard(role):
    if role == 'Citizen':
        return redirect(url_for('citizen_dashboard'))
    if role == 'Ward Member':
        return redirect(url_for('ward_dashboard'))
    if role == 'Department Officer':
        return redirect(url_for('officer_dashboard'))
    if role == 'President':
        return redirect(url_for('president_dashboard'))
    if role == 'Admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('index'))


def seed_demo_users():
    demo_users = [
        {'name': 'Citizen', 'email': 'citizen@test.com', 'password': 'citizen123', 'role': 'Citizen', 'ward_number': 1},
        {'name': 'Ward Member', 'email': 'ward@test.com', 'password': 'ward123', 'role': 'Ward Member', 'ward_number': 1},
        {
            'name': 'Department Officer',
            'email': 'officer@test.com',
            'password': 'officer123',
            'role': 'Department Officer',
            'department': 'Sanitation',
        },
        {'name': 'President', 'email': 'president@test.com', 'password': 'president123', 'role': 'President'},
        {'name': 'Admin', 'email': 'admin@test.com', 'password': 'admin123', 'role': 'Admin'},
    ]
    for user_data in demo_users:
        if not User.query.filter_by(email=user_data['email']).first():
            db.session.add(
                User(
                    name=user_data['name'],
                    email=user_data['email'],
                    password=hash_password(user_data['password']),
                    role=user_data['role'],
                    ward_number=user_data.get('ward_number'),
                    department=user_data.get('department'),
                )
            )
    db.session.commit()


def register_cli_commands(app):
    @app.cli.command('seed-demo-data')
    def seed_demo_data_command():
        """Seed demo users for local development only."""
        if isinstance(app.config.get('ACTIVE_CONFIG_CLASS'), type) and app.config['ACTIVE_CONFIG_CLASS'] is ProductionConfig:
            raise RuntimeError('Demo data seeding is disabled for production configuration.')

        with app.app_context():
            seed_demo_users()
        print('Demo users seeded.')


def register_routes(app):
    @app.route('/')
    def index():
        return render_template('public_dashboard.html')

    @app.route('/login', methods=['GET', 'POST'])
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

    @app.route('/register', methods=['GET', 'POST'])
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
                return redirect(url_for('register'))

            if User.query.filter_by(email=email).first():
                flash('Email already registered')
                return redirect(url_for('register'))

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
            return redirect(url_for('citizen_dashboard'))
        return render_template('register.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/citizen_dashboard')
    @login_required
    def citizen_dashboard():
        if current_user.role != 'Citizen':
            return redirect_dashboard(current_user.role)
        complaints = Complaint.query.filter_by(user_id=current_user.id).all()
        return render_template('citizen_dashboard.html', complaints=complaints)

    @app.route('/submit_complaint', methods=['GET', 'POST'])
    @login_required
    def submit_complaint():
        if current_user.role != 'Citizen':
            return redirect_dashboard(current_user.role)
        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            category = request.form.get('category')
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')

            image = request.files.get('image')
            image_filename = None
            if image and image.filename != '':
                ext = image.filename.rsplit('.', 1)[1] if '.' in image.filename else 'jpg'
                image_filename = f"{uuid.uuid4().hex}.{ext}"
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

            department, priority = classify_department_and_priority(title + ' ' + description)

            complaint = Complaint(
                complaint_id=f"CMP-{uuid.uuid4().hex[:8].upper()}",
                title=title,
                description=description,
                category=category,
                department=department,
                ward_number=current_user.ward_number or 1,
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None,
                image_filename=image_filename,
                priority=priority,
                user_id=current_user.id,
            )
            db.session.add(complaint)
            db.session.commit()
            flash('Complaint submitted successfully')
            return redirect(url_for('citizen_dashboard'))

        return render_template('submit_complaint.html')

    @app.route('/ward_dashboard')
    @login_required
    def ward_dashboard():
        if current_user.role != 'Ward Member':
            return redirect_dashboard(current_user.role)
        complaints = Complaint.query.filter_by(ward_number=current_user.ward_number).all()
        status_options = {c.id: get_status_options_for_complaint(current_user, c) for c in complaints}
        return render_template('ward_dashboard.html', complaints=complaints, status_options=status_options)

    @app.route('/officer_dashboard')
    @login_required
    def officer_dashboard():
        if current_user.role != 'Department Officer':
            return redirect_dashboard(current_user.role)
        complaints = Complaint.query.all()
        status_options = {c.id: get_status_options_for_complaint(current_user, c) for c in complaints}
        return render_template('officer_dashboard.html', complaints=complaints, status_options=status_options)

    @app.route('/president_dashboard')
    @login_required
    def president_dashboard():
        if current_user.role != 'President':
            return redirect_dashboard(current_user.role)
        complaints = Complaint.query.all()
        status_options = {c.id: get_status_options_for_complaint(current_user, c) for c in complaints}
        return render_template('president_dashboard.html', complaints=complaints, status_options=status_options)

    @app.route('/admin_dashboard')
    @login_required
    def admin_dashboard():
        if current_user.role != 'Admin':
            return redirect_dashboard(current_user.role)
        users = User.query.all()
        complaints = Complaint.query.all()
        return render_template('admin_dashboard.html', users=users, complaints=complaints)

    @app.route('/update_complaint/<int:id>', methods=['POST'])
    @login_required
    def update_complaint(id):
        complaint = Complaint.query.get_or_404(id)
        status = request.form.get('status')
        if not can_user_update_complaint(current_user, complaint):
            abort(403)

        if status not in ALLOWED_STATUSES:
            flash('Invalid complaint status selected.')
            return redirect(request.referrer or redirect_dashboard(current_user.role))

        allowed_transitions = ROLE_STATUS_TRANSITIONS.get(current_user.role, {}).get(complaint.status, set())
        if status not in allowed_transitions:
            flash('You are not allowed to set this status for the selected complaint.')
            return redirect(request.referrer or redirect_dashboard(current_user.role))

        complaint.status = status
        db.session.commit()
        flash(f'Complaint {complaint.complaint_id} status updated to {status}')
        return redirect(request.referrer or redirect_dashboard(current_user.role))

    @app.route('/map')
    def view_map():
        complaints = Complaint.query.all()
        complaints_data = []
        for complaint in complaints:
            if complaint.latitude and complaint.longitude:
                complaints_data.append(
                    {
                        'id': complaint.complaint_id,
                        'title': complaint.title,
                        'lat': complaint.latitude,
                        'lng': complaint.longitude,
                        'status': complaint.status,
                        'priority': complaint.priority,
                    }
                )
        return render_template('map.html', complaints=complaints_data)

    @app.route('/analytics')
    def analytics():
        total = Complaint.query.count()
        pending = Complaint.query.filter(Complaint.status != 'Resolved').count()
        resolved = Complaint.query.filter_by(status='Resolved').count()
        return render_template('analytics.html', total=total, pending=pending, resolved=resolved)

    @app.route('/complaints')
    def public_complaints():
        complaints = Complaint.query.order_by(Complaint.timestamp.desc()).all()
        return render_template('complaints.html', complaints=complaints)


def resolve_config_class():
    config_name = os.environ.get('APP_CONFIG')
    if config_name:
        return CONFIG_BY_NAME.get(config_name.lower(), DevelopmentConfig)

    flask_env = os.environ.get('FLASK_ENV', 'development').lower()
    return CONFIG_BY_NAME.get(flask_env, DevelopmentConfig)


def create_app():
    app = Flask(__name__)
    config_class = resolve_config_class()
    app.config.from_object(config_class)
    app.config['ACTIVE_CONFIG_CLASS'] = config_class

    if config_class is ProductionConfig:
        ProductionConfig.validate()

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'login'

    register_routes(app)
    register_cli_commands(app)

    with app.app_context():
        db.create_all()
        should_seed_demo_data = os.environ.get('SEED_DEMO_DATA', 'false').lower() == 'true'
        if should_seed_demo_data and config_class is not ProductionConfig:
            seed_demo_users()

    return app
