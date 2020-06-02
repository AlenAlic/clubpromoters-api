from flask_restx import Namespace, Resource, abort, fields
from flask_login import current_user
from ext import db
from models import login_required, requires_access_level, ACCESS_HOSTESS
from models import Party, Purchase
from datetime import datetime


api = Namespace("hostess", description="Hostess")


@api.route("/parties")
class HostessAPIParties(Resource):

    @api.response(200, "List of parties for the night")
    @login_required
    @requires_access_level(ACCESS_HOSTESS)
    def get(self):
        """Get list of parties for today"""
        parties = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime > datetime.utcnow(),
                                     Party.club_owner_id == current_user.club_owner_id) \
            .order_by(Party.party_start_datetime).all()
        parties = [p for p in parties if p.party_start_datetime.date() >= datetime.utcnow().date()]
        return [p.json() for p in parties]


@api.route("/party/<int:party_id>")
class HostessAPIParty(Resource):

    @api.response(200, "Party")
    @login_required
    @requires_access_level(ACCESS_HOSTESS)
    def get(self, party_id):
        """Get list of parties for today"""
        party = Party.query.filter(Party.party_id == party_id).first()
        return {
            "party": party.json(),
            "purchases": [p.json() for p in party.purchases],
        }


@api.route("/entrance_code")
class HostessAPIEntranceCode(Resource):

    @api.expect(api.model("EntranceCode", {
        "entrance_code": fields.String(required=True),
    }), validate=True)
    @api.response(200, "Purchase")
    @api.response(400, "Entrance code not valid")
    @api.response(404, "Purchase not found")
    @login_required
    @requires_access_level(ACCESS_HOSTESS)
    def post(self):
        """Get purchase from scanning QR code"""
        purchase = Purchase.query.filter(Purchase.hash == api.payload["entrance_code"]).first()
        if not purchase:
            return abort(404)
        available_tickets = [t for t in purchase.tickets if t.available()]
        if len(available_tickets) > 0:
            return purchase.json()
        return abort(400)


@api.route("/accept")
class HostessAPIAccept(Resource):

    @api.expect(api.model("Accept", {
        "purchase_id": fields.String(required=True),
        "tickets": fields.Integer(required=True),
    }), validate=True)
    @api.response(200, "Purchase")
    @api.response(400, "Cannot accept more tickets than are available")
    @login_required
    @requires_access_level(ACCESS_HOSTESS)
    def post(self):
        """Accept a number of tickets"""
        purchase = Purchase.query.filter(Purchase.purchase_id == api.payload["purchase_id"]).first()
        tickets = api.payload["tickets"]
        available_tickets = [t for t in purchase.tickets if t.available()]
        if len(available_tickets) >= tickets:
            for i in range(tickets):
                available_tickets[i].used = True
            db.session.commit()
            return
        return abort(400)


@api.route("/deny")
class HostessAPIDeny(Resource):

    @api.expect(api.model("Deny", {
        "purchase_id": fields.String(required=True),
        "tickets": fields.Integer(required=True),
    }), validate=True)
    @api.response(200, "Purchase")
    @api.response(400, "Cannot deny more tickets than are available")
    @login_required
    @requires_access_level(ACCESS_HOSTESS)
    def post(self):
        """Deny a number of tickets"""
        purchase = Purchase.query.filter(Purchase.purchase_id == api.payload["purchase_id"]).first()
        tickets = api.payload["tickets"]
        available_tickets = [t for t in purchase.tickets if t.available()]
        if len(available_tickets) >= tickets:
            for i in range(tickets):
                available_tickets[i].denied_entry = True
            db.session.commit()
            return
        return abort(400)
