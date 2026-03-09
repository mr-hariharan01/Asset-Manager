from flask import redirect, url_for


def redirect_dashboard(role):
    if role == 'Citizen':
        return redirect(url_for('dashboards.citizen_dashboard'))
    elif role == 'Ward Member':
        return redirect(url_for('dashboards.ward_dashboard'))
    elif role == 'Department Officer':
        return redirect(url_for('dashboards.officer_dashboard'))
    elif role == 'President':
        return redirect(url_for('dashboards.president_dashboard'))
    elif role == 'Admin':
        return redirect(url_for('dashboards.admin_dashboard'))
    return redirect(url_for('public.index'))
