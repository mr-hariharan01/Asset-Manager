import unittest

from project import create_app
from project.extensions import db
from project.models import User
from project.services.security import hash_password


class RouteModuleTests(unittest.TestCase):
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

    def _login_citizen(self):
        user = User(name='Citizen', email='cit@test.com', password=hash_password('pass123'), role='Citizen', ward_number=1)
        db.session.add(user)
        db.session.commit()
        return self.client.post('/login', data={'email': 'cit@test.com', 'password': 'pass123'})

    def test_public_endpoints_available(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/analytics').status_code, 200)
        self.assertEqual(self.client.get('/complaints').status_code, 200)

    def test_submit_complaint_requires_auth(self):
        response = self.client.get('/submit_complaint')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])

    def test_submit_complaint_for_citizen(self):
        self._login_citizen()
        response = self.client.post(
            '/submit_complaint',
            data={
                'title': 'Water leak',
                'description': 'Pipe leak in ward',
                'category': 'Water',
                'latitude': '10.2',
                'longitude': '76.3',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/citizen_dashboard', response.headers['Location'])


if __name__ == '__main__':
    unittest.main()
