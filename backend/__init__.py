from flask import Flask
from flask_login import current_user
from config import Config
from constants import *
from datetime import datetime
from ext import db, migrate, login, mail, cors
import commands
import os
from utilities import cents_to_euro
import base64


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

    # Template filters and constants
    add_template_filters_and_constants(app)

    # Create static folders (if not available)
    make_folders(app)

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

    from backend.invoices import bp as invoices_bp
    app.register_blueprint(invoices_bp, url_prefix="/invoices")

    from backend.settings import bp as settings_bp
    app.register_blueprint(settings_bp, url_prefix="/settings")

    from backend.downloads import bp as downloads_bp
    app.register_blueprint(downloads_bp, url_prefix="/downloads")

    if app.config.get("DEBUG"):
        from backend.testing import bp as testing_bp
        app.register_blueprint(testing_bp, url_prefix="/testing")

        from backend.preview import bp as preview_bp
        app.register_blueprint(preview_bp, url_prefix="/preview")

    if app.config.get("DEMO"):
        from backend.demo import bp as demo_bp
        app.register_blueprint(demo_bp, url_prefix="/demo")

    import apis
    apis.init_app(app)


def add_template_filters_and_constants(app):
    # Converting prices to euro
    @app.template_filter("euro_format")
    def euro_format(p):
        return "€{:,.2f}".format(p)

    # Converting prices to euro
    @app.template_filter("cents_to_euro")
    def euro_cents_to_euro(c):
        return cents_to_euro(c)

    # General email logo
    @app.context_processor
    def inject_email_logo():
        path = os.path.join(app.static_folder, "email_logo.png")
        return dict(email_logo=base64.b64encode(open(path, "rb").read()).decode())


def make_folders(app):
    generated = "generated"
    generated_path = os.path.join(app.root_path, generated)
    app.uploads_folder = os.path.join(app.static_folder, UPLOAD_FOLDER)
    app.receipts_folder = os.path.join(generated_path, RECEIPTS_FOLDER)
    app.invoices_folder = os.path.join(generated_path, INVOICES_FOLDER)
    app.tickets_folder = os.path.join(generated_path, TICKETS_FOLDER)

    # Uploads
    if not os.path.exists(app.uploads_folder):
        os.makedirs(app.uploads_folder)
    # Receipts
    if not os.path.exists(app.receipts_folder):
        os.makedirs(app.receipts_folder)
    # Invoices
    if not os.path.exists(app.invoices_folder):
        os.makedirs(app.invoices_folder)
    # Tickets
    if not os.path.exists(app.tickets_folder):
        os.makedirs(app.tickets_folder)
