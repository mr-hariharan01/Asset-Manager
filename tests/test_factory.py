import unittest

from project import create_app


class AppFactoryTests(unittest.TestCase):
    def test_create_app_registers_blueprints(self):
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        self.assertIn('auth', app.blueprints)
        self.assertIn('complaints', app.blueprints)
        self.assertIn('public', app.blueprints)
        self.assertIn('dashboards', app.blueprints)
        self.assertEqual(app.login_manager.login_view, 'auth.login')


if __name__ == '__main__':
    unittest.main()
