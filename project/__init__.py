import os

from flask import Flask

from project.extensions import db, login_manager
from project.models import User
from project.routes.auth import bp as auth_bp
from project.routes.complaints import bp as complaints_bp
from project.routes.dashboards import bp as dashboards_bp
from project.routes.public import bp as public_bp
from project.services.security import hash_password


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def _seed_demo_users():
    demo_users = [
        {
            'name': 'Citizen',
            'email': 'citizen@test.com',
            'password': 'citizen123',
            'role': 'Citizen',
            'ward_number': 1,
        },
        {
            'name': 'Ward Member',
            'email': 'ward@test.com',
            'password': 'ward123',
            'role': 'Ward Member',
            'ward_number': 1,
        },
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
    for u in demo_users:
        if not User.query.filter_by(email=u['email']).first():
            user = User(
                name=u['name'],
                email=u['email'],
                password=hash_password(u['password']),
                role=u['role'],
                ward_number=u.get('ward_number'),
                department=u.get('department'),
            )
            db.session.add(user)
    db.session.commit()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True, template_folder='../templates', static_folder='../static')
    app.config.from_mapping(
        SECRET_KEY='supersecretkey',
        SQLALCHEMY_DATABASE_URI='sqlite:///database.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER='static/uploads',
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboards_bp)
    app.register_blueprint(complaints_bp)

    with app.app_context():
        db.create_all()
        if not app.config.get('TESTING'):
            _seed_demo_users()

    return app
