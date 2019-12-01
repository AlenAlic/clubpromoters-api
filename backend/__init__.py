from flask import Flask, g, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, AnonymousUserMixin, current_user
from flask_mail import Mail
from config import Config
from backend.values import *
from datetime import datetime


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
mail = Mail()


class Anonymous(AnonymousUserMixin):

    @staticmethod
    def is_admin():
        return False

    @staticmethod
    def profile():
        return None


def create_app(config_class=Config):
    from backend.models import User

    app = Flask(__name__)
    app.config.from_object(config_class)
    app.url_map.strict_slashes = False

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:'))
    login.init_app(app)
    login.anonymous_user = Anonymous
    mail.init_app(app)

    @app.before_request
    def before_request_callback():
        g.values = values
        if current_user.is_authenticated:
            current_user.last_seen = datetime.utcnow()
            db.session.commit()

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')
        if origin and origin in config_class.ALLOWED_URLS:
            response.headers['Access-Control-Allow-Origin'] = origin
        if request.method == 'OPTIONS':
            response.headers['Access-Control-Allow-Methods'] = 'DELETE, GET, POST, PUT, PATCH'
            headers = request.headers.get('Access-Control-Request-Headers')
            if headers:
                response.headers['Access-Control-Allow-Headers'] = headers
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

    app.after_request(add_cors_headers)

    @app.shell_context_processor
    def make_shell_context():
        return {
            'create_admin': create_admin
        }

    def create_admin(email, password, first_name, last_name):
        if len(User.query.filter(User.access == values.AL_ADMIN).all()) == 0:
            a = User()
            a.email = email
            a.set_password(password)
            a.access = values.AL_ADMIN
            a.is_active = True
            a.first_name = first_name
            a.last_name = last_name
            db.session.add(a)
            db.session.commit()

    from backend.main import bp as main_bp
    app.register_blueprint(main_bp)

    from backend.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app


# noinspection PyPep8
from backend import models
