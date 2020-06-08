from flask import Flask
from flask_login import current_user
from config import Config
from constants import *
from datetime import datetime
from ext import db, migrate, login, mail, cors
import commands
import os
from utilities import cents_to_euro


def create_app(config_class=Config):

    # Create and configure the app
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.url_map.strict_slashes = False

    configure_extensions(app)

    # Update when a authenticated user was last seen before each request
    @app.before_request
    def before_request_callback():
        if current_user.is_authenticated:
            current_user.last_seen = datetime.utcnow()
            db.session.commit()

    # Template filters
    # Converting prices to euro
    @app.template_filter("euro_format")
    def euro_format(p):
        return "€{:,.2f}".format(p)
    # Converting prices to euro
    @app.template_filter("cents_to_euro")
    def euro_cents_to_euro(c):
        return cents_to_euro(c)

    # Create static folders (if not available)
    make_static_folders(app)

    # Register blueprints, API, and sockets
    register_blueprints(app)

    return app


def configure_extensions(app):
    from models import Anonymous
    import admin

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"))
    login.init_app(app)
    login.login_view = "main.index"
    login.login_message = None
    login.anonymous_user = Anonymous
    admin.init_app(app, db)
    mail.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    commands.init_app(app)


def register_blueprints(app):
    from backend.main import bp as main_bp
    app.register_blueprint(main_bp)

    from backend.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from backend.email import bp as email_bp
    app.register_blueprint(email_bp, url_prefix="/email")

    from backend.receipts import bp as receipts_bp
    app.register_blueprint(receipts_bp, url_prefix="/receipts")

    from backend.settings import bp as settings_bp
    app.register_blueprint(settings_bp, url_prefix="/settings")

    if app.config.get("DEBUG"):
        from backend.testing import bp as testing_bp
        app.register_blueprint(testing_bp, url_prefix="/testing")

    import apis
    apis.init_app(app)


def make_static_folders(app):
    # Uploads
    directory = os.path.join(app.static_folder, UPLOAD_FOLDER)
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Receipts
    directory = os.path.join(app.static_folder, RECEIPTS_FOLDER)
    if not os.path.exists(directory):
        os.makedirs(directory)
