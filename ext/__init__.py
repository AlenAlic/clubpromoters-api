from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
mail = Mail()
cors = CORS()
