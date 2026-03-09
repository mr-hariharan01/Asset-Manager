from flask import Blueprint, render_template
from flask_login import current_user, login_required

from project.models import Complaint, User
from project.services.navigation import redirect_dashboard

bp = Blueprint('dashboards', __name__)


@bp.route('/citizen_dashboard')
@login_required
def citizen_dashboard():
    if current_user.role != 'Citizen':
        return redirect_dashboard(current_user.role)
    complaints = Complaint.query.filter_by(user_id=current_user.id).all()
    return render_template('citizen_dashboard.html', complaints=complaints)


@bp.route('/ward_dashboard')
@login_required
def ward_dashboard():
    if current_user.role != 'Ward Member':
        return redirect_dashboard(current_user.role)
    complaints = Complaint.query.filter_by(ward_number=current_user.ward_number).all()
    return render_template('ward_dashboard.html', complaints=complaints)


@bp.route('/officer_dashboard')
@login_required
def officer_dashboard():
    if current_user.role != 'Department Officer':
        return redirect_dashboard(current_user.role)
    complaints = Complaint.query.all()
    return render_template('officer_dashboard.html', complaints=complaints)


@bp.route('/president_dashboard')
@login_required
def president_dashboard():
    if current_user.role != 'President':
        return redirect_dashboard(current_user.role)
    complaints = Complaint.query.all()
    return render_template('president_dashboard.html', complaints=complaints)


@bp.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'Admin':
        return redirect_dashboard(current_user.role)
    users = User.query.all()
    complaints = Complaint.query.all()
    return render_template('admin_dashboard.html', users=users, complaints=complaints)
