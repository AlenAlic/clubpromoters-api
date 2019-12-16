from flask import request, g, abort
from backend.mollie_webhook import bp
from backend import db
from backend.models import Purchase
from mollie.api.client import Client
from mollie.api.error import Error
from backend.mollie_webhook.email import send_purchased_tickets


@bp.route('/mollie_webhook', methods=['POST'])
def mollie_webhook():
    try:
        mollie_client = Client()
        mollie_client.set_api_key(g.mollie)
        if 'id' not in request.form:
            abort(404, 'Unknown payment id')
        payment_id = request.form['id']
        payment = mollie_client.payments.get(payment_id)
        purchase = Purchase.query.filter(Purchase.purchase_id == payment.metadata["purchase_id"]).first()
        if purchase is not None:
            if payment.is_paid():
                # At this point you'd probably want to start the process of delivering the product to the customer.
                purchase.purchase_paid()
                db.session.commit()
                send_purchased_tickets(purchase)
                return 'Paid'
            elif payment.is_pending():
                # The payment has started but is not complete yet.
                purchase.purchase_pending()
                db.session.commit()
                return 'Pending'
            elif payment.is_open():
                # The payment has not started yet. Wait for it.
                return 'Open'
            else:
                # The payment has been unsuccessful.
                purchase.cancel_purchase()
                db.session.commit()
                return 'Cancelled'
        abort(404, 'Unknown purchase')
    except Error as e:
        return 'Mollie Webhook call failed: {error}'.format(error=e)
