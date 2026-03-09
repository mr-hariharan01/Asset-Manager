import os
import uuid

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from project.extensions import db
from project.models import Complaint
from project.services.classification import classify_department_and_priority
from project.services.navigation import redirect_dashboard

bp = Blueprint('complaints', __name__)


@bp.route('/submit_complaint', methods=['GET', 'POST'])
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
            image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))

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
        return redirect(url_for('dashboards.citizen_dashboard'))

    return render_template('submit_complaint.html')


@bp.route('/update_complaint/<int:id>', methods=['POST'])
@login_required
def update_complaint(id):
    complaint = Complaint.query.get_or_404(id)
    status = request.form.get('status')
    if status:
        complaint.status = status
        db.session.commit()
        flash(f'Complaint {complaint.complaint_id} status updated to {status}')
    return redirect(request.referrer)


@bp.route('/complaints')
def public_complaints():
    complaints = Complaint.query.order_by(Complaint.timestamp.desc()).all()
    return render_template('complaints.html', complaints=complaints)
