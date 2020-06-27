import os
import json
# noinspection PyPackageRequirements
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):

    ENV = os.environ.get('ENV') or 'development'
    DEBUG = os.environ.get('DEBUG') == "True" or False

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///' + os.path.join(basedir, 'app.db')

    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = False

    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'localhost'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 8025)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or ''
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or ''
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or ''
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'email@example.com'

    ERROR_EMAIL = os.environ.get("ERROR_EMAIL") or "error@example.com"

    FLASK_ADMIN_FLUID_LAYOUT = True
    FLASK_ADMIN_SWATCH = "flatly"

    PRETTY_URL = os.environ.get('PRETTY_URL') or "127.0.0.1:8080"
    BASE_URL = "https://" + PRETTY_URL
    ACTIVATE_URL = BASE_URL + "/activate/"
    RESET_URL = BASE_URL + "/password/reset/"

    allowed_urls = os.environ.get("ALLOWED_URLS")
    ALLOWED_URLS = json.loads(allowed_urls) if allowed_urls else ["http://127.0.0.1:8080"]

    # DEV ONLY
    # The Mollie API key is set in the config
    MOLLIE_API_KEY = os.environ.get('MOLLIE_API_KEY')
    # Mollie web hook url
    MOLLIE_WEB_HOOK_URL = os.environ.get('MOLLIE_WEB_HOOK_URL')

    MAX_CONTENT_LENGTH = 25 * 1024 * 1024


# MAIL SERVERS
# python -m smtpd -n -c DebuggingServer localhost:8025
# python -u -m smtpd -n -c DebuggingServer localhost:8025 > mail.log

# requirements
# pip freeze > requirements.txt
