from flask_restx import Namespace, Resource
from flask_login import current_user
from models import login_required, requires_access_level, ACCESS_CLUB_OWNER, ACCESS_PROMOTER
from models import Invoice


api = Namespace("invoices", description="All invoices belonging to a Club Owner or Promoter")


@api.route("")
class InvoiceAPI(Resource):

    @api.response(200, "All invoices of a user")
    @login_required
    @requires_access_level(ACCESS_CLUB_OWNER, ACCESS_PROMOTER)
    def get(self):
        """All invoices"""
        invoices = Invoice.query.filter(Invoice.user == current_user).all()
        return [i.json() for i in invoices]
