import unittest

from project import create_app
from project.extensions import db
from project.models import User
from project.services.security import hash_password


class AuthRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_register_creates_citizen(self):
        response = self.client.post(
            '/register',
            data={
                'name': 'New User',
                'email': 'new@test.com',
                'phone': '123',
                'password': 'secret',
                'confirm_password': 'secret',
                'district': 'D',
                'panchayat': 'P',
                'ward_number': '1',
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(User.query.filter_by(email='new@test.com').first())

    def test_login_redirects_by_role(self):
        user = User(name='Admin', email='admin@test.com', password=hash_password('admin123'), role='Admin')
        db.session.add(user)
        db.session.commit()

        response = self.client.post('/login', data={'email': 'admin@test.com', 'password': 'admin123'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin_dashboard', response.headers['Location'])


if __name__ == '__main__':
    unittest.main()
