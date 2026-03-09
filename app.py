from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User, Complaint, Feedback
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import bcrypt
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

DEPARTMENT_ALIASES = {
    'electricity': 'Electricity Department',
    'electricity department': 'Electricity Department',
    'sanitation': 'Sanitation Department',
    'sanitation department': 'Sanitation Department',
    'public works': 'Public Works Department',
    'public works department': 'Public Works Department',
    'water supply': 'Water Supply Department',
    'water supply department': 'Water Supply Department',
    'general': 'General',
}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def normalize_department_name(department):
    if not department:
        return None
    return DEPARTMENT_ALIASES.get(department.strip().lower(), department.strip())

with app.app_context():
    db.create_all()
    # Create demo accounts
    demo_users = [
        {'name': 'Citizen', 'email': 'citizen@test.com', 'password': 'citizen123', 'role': 'Citizen', 'ward_number': 1},
        {'name': 'Ward Member', 'email': 'ward@test.com', 'password': 'ward123', 'role': 'Ward Member', 'ward_number': 1},
        {'name': 'Department Officer', 'email': 'officer@test.com', 'password': 'officer123', 'role': 'Department Officer', 'department': 'Sanitation Department'},
        {'name': 'President', 'email': 'president@test.com', 'password': 'president123', 'role': 'President'},
        {'name': 'Admin', 'email': 'admin@test.com', 'password': 'admin123', 'role': 'Admin'}
    ]
    for u in demo_users:
        if not User.query.filter_by(email=u['email']).first():
            user = User(
                name=u['name'],
                email=u['email'],
                password=hash_password(u['password']),
                role=u['role'],
                ward_number=u.get('ward_number'),
                department=normalize_department_name(u.get('department'))
            )
            db.session.add(user)

    for user in User.query.filter(User.department.isnot(None)).all():
        user.department = normalize_department_name(user.department)

    for complaint in Complaint.query.all():
        complaint.department = normalize_department_name(complaint.department) or 'General'

    db.session.commit()

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
            ward_number=int(ward_number) if ward_number else None
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

def redirect_dashboard(role):
    if role == 'Citizen': return redirect(url_for('citizen_dashboard'))
    elif role == 'Ward Member': return redirect(url_for('ward_dashboard'))
    elif role == 'Department Officer': return redirect(url_for('officer_dashboard'))
    elif role == 'President': return redirect(url_for('president_dashboard'))
    elif role == 'Admin': return redirect(url_for('admin_dashboard'))
    return redirect(url_for('index'))

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

@app.route('/citizen_dashboard')
@login_required
def citizen_dashboard():
    if current_user.role != 'Citizen': return redirect_dashboard(current_user.role)
    complaints = Complaint.query.filter_by(user_id=current_user.id).all()
    return render_template('citizen_dashboard.html', complaints=complaints)

@app.route('/submit_complaint', methods=['GET', 'POST'])
@login_required
def submit_complaint():
    if current_user.role != 'Citizen': return redirect_dashboard(current_user.role)
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
            
        department, priority = classify_department_and_priority(title + " " + description)
        
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
            user_id=current_user.id
        )
        db.session.add(complaint)
        db.session.commit()
        flash('Complaint submitted successfully')
        return redirect(url_for('citizen_dashboard'))
        
    return render_template('submit_complaint.html')

@app.route('/ward_dashboard')
@login_required
def ward_dashboard():
    if current_user.role != 'Ward Member': return redirect_dashboard(current_user.role)
    complaints = Complaint.query.filter_by(ward_number=current_user.ward_number).all()
    return render_template('ward_dashboard.html', complaints=complaints)

@app.route('/officer_dashboard')
@login_required
def officer_dashboard():
    if current_user.role != 'Department Officer': return redirect_dashboard(current_user.role)
    officer_department = normalize_department_name(current_user.department)
    complaints = Complaint.query.filter_by(department=officer_department).all() if officer_department else []
    return render_template('officer_dashboard.html', complaints=complaints, officer_department=officer_department)

@app.route('/president_dashboard')
@login_required
def president_dashboard():
    if current_user.role != 'President': return redirect_dashboard(current_user.role)
    complaints = Complaint.query.all()
    return render_template('president_dashboard.html', complaints=complaints)

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'Admin': return redirect_dashboard(current_user.role)
    users = User.query.all()
    complaints = Complaint.query.all()
    return render_template('admin_dashboard.html', users=users, complaints=complaints)

@app.route('/update_complaint/<int:id>', methods=['POST'])
@login_required
def update_complaint(id):
    complaint = Complaint.query.get_or_404(id)
    status = request.form.get('status')
    if status:
        complaint.status = status
        db.session.commit()
        flash(f'Complaint {complaint.complaint_id} status updated to {status}')
    return redirect(request.referrer)

@app.route('/map')
def view_map():
    complaints = Complaint.query.all()
    complaints_data = []
    for c in complaints:
        if c.latitude and c.longitude:
            complaints_data.append({
                'id': c.complaint_id,
                'title': c.title,
                'lat': c.latitude,
                'lng': c.longitude,
                'status': c.status,
                'priority': c.priority
            })
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
