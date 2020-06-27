from flask_restx import Namespace, Resource, abort
from ext import db
from flask import request, abort
from models import Purchase
from mollie.api.client import Client
from .email import send_purchased_tickets, send_receipt
from constants.mollie import STATUS_PAID, STATUS_PENDING, STATUS_OPEN, STATUS_CANCELED
from models.configuration import config


api = Namespace("mollie", description="Mollie interaction")


@api.route("/webhook")
class MollieAPIWebhook(Resource):

    @api.doc(security=None)
    @api.response(200, "Redirected to Mollie")
    @api.response(404, "Purchase not found")
    def post(self):
        """Create purchase and send data to Mollie"""
        conf = config()
        mollie_client = Client()
        mollie_client.set_api_key(conf.mollie)
        if "id" not in request.form:
            abort(404, "Unknown payment id")
        payment_id = request.form["id"]
        payment = mollie_client.payments.get(payment_id)
        purchase = Purchase.query.filter(Purchase.purchase_id == payment.metadata["purchase_id"]).first()
        if purchase is not None:
            if payment.is_paid():
                if not purchase.status == STATUS_PAID:
                    # Start the process of delivering the product to the customer.
                    purchase.purchase_paid()
                    db.session.commit()
                    purchase.generate_receipt()
                    db.session.commit()
                    purchase.generate_tickets()
                    db.session.commit()
                    send_receipt(purchase)
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
        return
