from flask_restx import Namespace, Resource, abort, fields
from ext import db
from flask import request, g, abort
from models import Purchase
from mollie.api.client import Client
from mollie.api.error import Error
from .email import send_purchased_tickets
from constants.mollie import STATUS_PAID, STATUS_PENDING, STATUS_OPEN, STATUS_CANCELED


api = Namespace("mollie", description="Mollie interaction")


@api.route("/webhook")
class MollieAPIWebhook(Resource):

    @api.doc(security=None)
    @api.expect(api.model("MollieWebhook", {
        "id": fields.String(required=True),
    }), validate=True)
    @api.response(200, "Redirected to Mollie")
    @api.response(404, "Purchase not found")
    def post(self):
        """Create purchase and send data to Mollie"""
        try:
            mollie_client = Client()
            mollie_client.set_api_key(g.mollie)
            if "id" not in request.form:
                abort(404, "Unknown payment id")
            payment_id = api.payload["id"]
            payment = mollie_client.payments.get(payment_id)
            purchase = Purchase.query.filter(Purchase.purchase_id == payment.metadata["purchase_id"]).first()
            if purchase is not None:
                if payment.is_paid():
                    # At this point you'd probably want to start the process of delivering the product to the customer.
                    purchase.purchase_paid()
                    db.session.commit()
                    send_purchased_tickets(purchase)
                    return STATUS_PAID
                elif payment.is_pending():
                    # The payment has started but is not complete yet.
                    purchase.purchase_pending()
                    db.session.commit()
                    return STATUS_PENDING
                elif payment.is_open():
                    # The payment has not started yet. Wait for it.
                    return STATUS_OPEN
                else:
                    # The payment has been unsuccessful.
                    purchase.cancel_purchase()
                    db.session.commit()
                    return STATUS_CANCELED
        except Error as e:
            return "Mollie Webhook call failed: {error}".format(error=e)
