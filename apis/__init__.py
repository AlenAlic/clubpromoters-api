from flask import Blueprint
from flask_restx import Api
from .auth import api as auth
from .ping import api as ping
from .user import api as user
from .club_owner import api as club_owner
from .documents import api as documents
from .hostess import api as hostess
from .promoter import api as promoter
from .public import api as public
from .purchase import api as purchase
from .admin import api as admin_api
from .mollie import api as mollie_api
from .organizer import api as organizer
from .code import api as code
from .invoices import api as invoices
from .files import api as files


authorizations = {
    "bearer": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization"
    }
}


bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(bp, doc="/doc", authorizations=authorizations, security="bearer",
          title="clubpromoters.net API", version="1.0")


api.add_namespace(admin_api)
api.add_namespace(auth)
api.add_namespace(club_owner)
api.add_namespace(code)
api.add_namespace(documents)
api.add_namespace(files)
api.add_namespace(hostess)
api.add_namespace(invoices)
api.add_namespace(mollie_api)
api.add_namespace(organizer)
api.add_namespace(ping)
api.add_namespace(promoter)
api.add_namespace(public)
api.add_namespace(purchase)
api.add_namespace(user)


def init_app(app):
    from .debug import api as debug
    if app.config.get("DEBUG"):
        api.add_namespace(debug)
    app.register_blueprint(bp)
