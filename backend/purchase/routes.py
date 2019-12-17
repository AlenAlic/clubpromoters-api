from flask import render_template, redirect, url_for, request, g, abort, json, current_app, jsonify
from backend.purchase import bp
from backend import db
from backend.models import code_required, Party, Ticket, Purchase, get_code_from_request
from mollie.api.client import Client
from backend.values import *


@bp.route('/order/<int:party_id>', methods=[POST])
@code_required
def order(party_id):
    form = json.loads(request.data)
    party = Party.query.filter(Party.party_id == party_id).first()
    tickets = form["tickets"]
    if party is not None and party.check_ticket_availability(tickets):
        purchase = Purchase()
        purchase.party = party
        purchase.email = form["email"]
        purchase.first_name = form["first_name"]
        purchase.last_name = form["last_name"]
        purchase.code = get_code_from_request(request)
        purchase.promoter = purchase.code.user
        purchase.set_commissions()
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
        payment = mollie_client.payments.create({
            'amount': {
                'currency': 'EUR',
                'value': purchase.mollie_price()
            },
            'description': f'{purchase.mollie_description()}',
            'webhookUrl': url_for('mollie_webhook.mollie_webhook', scheme='https', _external=True),
            'redirectUrl': f'{current_app.config.get("BASE_URL")}/purchase/completed/{purchase.hash}',
            'metadata': {
                'purchase_id': str(purchase.purchase_id),
            }
        })
        purchase.mollie_payment_id = payment.id
        db.session.commit()
        return payment.checkout_url
    return BAD_REQUEST


@bp.route('/completed/<purchase_hash>', methods=[GET])
def completed(purchase_hash=None):
    if purchase_hash is None:
        return NOT_FOUND
    purchase = Purchase.query.filter(Purchase.hash == purchase_hash).first()
    if purchase is not None:
        return jsonify(purchase.json())
    return BAD_REQUEST


@bp.route('/failed', methods=[GET])
def failed():
    return render_template('purchases/failed.html')


@bp.route('/qr_code/<purchase_hash>', methods=[GET])
def qr_code(purchase_hash=None):
    if purchase_hash is None:
        abort(404, 'Unknown purchase')
    purchase = Purchase.query.filter(Purchase.hash == purchase_hash).first()
    if purchase is not None:
        return render_template('purchases/completed.html', purchase=purchase)
    return redirect(url_for('purchases.failed'))


# payment = {
#     'amount': {
#         'currency': 'EUR',
#         'value': '120.00'
#     },
#     'description': 'My first API payment',
#     'webhookUrl': '{root}02-webhook-verification'.format(root=flask.request.url_root),
#     'redirectUrl': '{root}03-return-page?my_webshop_id={id}'.format(root=flask.request.url_root,
#                                                                     id=my_webshop_id),
#     'locale': 'optional',
#     'method': ['optional'],
#     'metadata': {
#         'my_webshop_id': str(my_webshop_id)
#     }
# }