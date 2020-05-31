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
    def is_organizer():
        return False

    @staticmethod
    def is_club_owner():
        return False

    @staticmethod
    def is_promoter():
        return False

    @staticmethod
    def is_hostess():
        return False

    @staticmethod
    def allowed(s):
        return False

    @staticmethod
    def profile():
        return None


def create_app(config_class=Config):
    from backend.models import User, Configuration

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

    @app.before_request
    def before_request_callback():
        g.values = values
        if current_user.is_authenticated:
            current_user.last_seen = datetime.utcnow()
            db.session.commit()
        config = Configuration.query.first()
        g.config = config
        g.mollie = config.mollie_api_key if config is not None else None

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
            'create_admin': create_admin,
            'create_config': create_config
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

    def create_config():
        if len(Configuration.query.all()) == 0:
            conf = Configuration()
            if app.config.get("MOLLIE_API_KEY") is not None:
                conf.mollie_api_key = app.config.get("MOLLIE_API_KEY")
            db.session.add(conf)
            db.session.commit()

    from backend.main import bp as main_bp
    app.register_blueprint(main_bp)

    from backend.documents import bp as documents_bp
    app.register_blueprint(documents_bp, url_prefix='/documents')

    from backend.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from backend.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from backend.organizer import bp as organizer_bp
    app.register_blueprint(organizer_bp, url_prefix='/organizer')

    from backend.purchase import bp as purchase_bp
    app.register_blueprint(purchase_bp, url_prefix='/purchase')

    from backend.mollie_webhook import bp as mollie_webhook_bp
    app.register_blueprint(mollie_webhook_bp)

    from backend.club_owner import bp as club_owner_bp
    app.register_blueprint(club_owner_bp, url_prefix='/club_owner')

    from backend.hostess import bp as hostess_bp
    app.register_blueprint(hostess_bp, url_prefix='/hostess')

    from backend.promoter import bp as promoter_bp
    app.register_blueprint(promoter_bp, url_prefix='/promoter')

    return app


# noinspection PyPep8
from backend import models
