from flask_restx import Namespace, Resource, abort
from flask import send_from_directory
from flask_login import current_user
from models.configuration import config
from models import login_required, requires_access_level, ACCESS_ORGANIZER, ACCESS_CLUB_OWNER, ACCESS_PROMOTER
from models import Invoice


api = Namespace("documents", description="Website documents")


@api.route("/terms")
class DocumentsAPITerms(Resource):

    @api.doc(security=None)
    @api.response(200, "Terms and conditions (as shown at checkout)")
    @api.response(404, "Terms and conditions not found")
    def get(self):
        """Terms and conditions"""
        file = config().terms
        if file:
            return send_from_directory(file.directory, filename=file.filename, cache_timeout=0)
        return abort(404)


@api.route("/invoice/<int:invoice_id>")
class DocumentsAPIInvoice(Resource):

    @api.response(200, "Invoice")
    @api.response(403, "Not allowed to download invoice")
    @api.response(404, "Invoice not found")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER, ACCESS_CLUB_OWNER, ACCESS_PROMOTER)
    def get(self, invoice_id):
        """Terms and conditions"""
        invoice = Invoice.query.filter(Invoice.invoice_id == invoice_id).first()
        if invoice:
            if current_user.access == ACCESS_ORGANIZER or current_user == invoice.user:
                return send_from_directory(invoice.directory, filename=invoice.filename, cache_timeout=0)
            return abort(403)
        return abort(404)
