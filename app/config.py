import os


class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = 'development'


class ProductionConfig(BaseConfig):
    ENV = 'production'

    @classmethod
    def validate(cls):
        if not cls.SECRET_KEY:
            raise RuntimeError('SECRET_KEY must be set in production.')


CONFIG_BY_NAME = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
