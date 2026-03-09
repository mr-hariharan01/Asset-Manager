from flask import Blueprint, render_template

from project.models import Complaint

bp = Blueprint('public', __name__)


@bp.route('/')
def index():
    return render_template('public_dashboard.html')


@bp.route('/map')
def view_map():
    complaints = Complaint.query.all()
    complaints_data = []
    for c in complaints:
        if c.latitude and c.longitude:
            complaints_data.append(
                {
                    'id': c.complaint_id,
                    'title': c.title,
                    'lat': c.latitude,
                    'lng': c.longitude,
                    'status': c.status,
                    'priority': c.priority,
                }
            )
    return render_template('map.html', complaints=complaints_data)


@bp.route('/analytics')
def analytics():
    total = Complaint.query.count()
    pending = Complaint.query.filter(Complaint.status != 'Resolved').count()
    resolved = Complaint.query.filter_by(status='Resolved').count()
    return render_template('analytics.html', total=total, pending=pending, resolved=resolved)
