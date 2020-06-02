from flask_restx import Namespace, Resource, abort, fields
from ext import db
from models import Party, Ticket, Purchase
from models import get_code_from_request, code_required
from flask import url_for, request, g, current_app, Response
from mollie.api.client import Client


api = Namespace("purchase", description="Purchase")


@api.route("/order/<int:party_id>")
class PurchaseAPIOrder(Resource):

    @api.doc(security=None)
    @api.expect(api.model("Order", {
        "tickets": fields.Integer(required=True),
        "email": fields.String(required=True),
        "first_name": fields.String(required=True),
        "last_name": fields.String(required=True),
        "ticket_price": fields.Float(required=True),
        "administration_costs": fields.Float(required=True),
    }), validate=True)
    @api.response(200, "Checkout url for Mollie")
    @api.response(400, "Not enough tickets available")
    @api.response(404, "Party not found")
    @code_required
    def post(self, party_id):
        """Create Purchase and redirect to Mollie"""
        party = Party.query.filter(Party.party_id == party_id).first()
        tickets = api.payload["tickets"]
        if party:
            if party.check_ticket_availability(tickets):
                purchase = Purchase()
                purchase.party = party
                purchase.email = api.payload["email"]
                purchase.first_name = api.payload["first_name"]
                purchase.last_name = api.payload["last_name"]
                purchase.code = get_code_from_request(request)
                purchase.promoter = purchase.code.user
                purchase.set_commissions()
                purchase.set_ticket_price(api.payload["ticket_price"])
                purchase.set_administration_costs(api.payload["administration_costs"])
                purchase.set_price(party.get_ticket_price() * tickets)
                for i in range(tickets):
                    t = Ticket()
                    t.number = i + 1
                    purchase.tickets.append(t)
                db.session.add(purchase)
                db.session.flush()
                purchase.set_hash()
                db.session.commit()
                mollie_client = Client()
                mollie_client.set_api_key(g.mollie)
                payment_data = {
                    "amount": {
                        "currency": "EUR",
                        "value": purchase.mollie_price()
                    },
                    "description": f"{purchase.mollie_description()}",
                    "webhookUrl": url_for("api.mollie_mollie_api_webhook", _scheme="https", _external=True),
                    "redirectUrl": f'{current_app.config.get("BASE_URL")}/purchase/completed/{purchase.hash}',
                    "metadata": {
                        "purchase_id": str(purchase.purchase_id),
                    }
                }
                if current_app.config.get("DEBUG"):
                    payment_data["webhookUrl"] = current_app.config.get("MOLLIE_WEB_HOOK_URL")
                payment = mollie_client.payments.create(payment_data)
                purchase.mollie_payment_id = payment.id
                db.session.commit()
                return payment.checkout_url
            return abort(400)
        return abort(404)


@api.route("/completed/<purchase_hash>")
class PurchaseAPICompleted(Resource):

    @api.doc(security=None)
    @api.response(200, "Purchase")
    @api.response(404, "Purchase not found")
    def get(self, purchase_hash):
        """Get purchase from hash"""
        purchase = Purchase.query.filter(Purchase.hash == purchase_hash).first()
        if purchase is not None:
            return purchase.json()
        return abort(404)


@api.route("/qr_code/<purchase_hash>")
class PurchaseAPIQRCode(Resource):

    @api.doc(security=None)
    @api.response(200, "Purchase")
    @api.response(404, "Purchase not found")
    def get(self, purchase_hash):
        """Get purchase QR code"""
        purchase = Purchase.query.filter(Purchase.hash == purchase_hash).first()
        if purchase is not None:
            resp = Response(content_type="image/png")
            resp.data = purchase.qr_code_image()
            return resp
        return abort(404)


# payment = {
#     "amount": {
#         "currency": "EUR",
#         "value": "120.00"
#     },
#     "description": "My first API payment",
#     "webhookUrl": "{root}02-webhook-verification".format(root=flask.request.url_root),
#     "redirectUrl": "{root}03-return-page?my_webshop_id={id}".format(root=flask.request.url_root, id=my_webshop_id),
#     "locale": "optional",
#     "method": ["optional"],
#     "metadata": {
#         "my_webshop_id": str(my_webshop_id)
#     }
# }
