from flask_restx import Namespace, Resource, abort, fields
from flask_login import current_user
from ext import db
from models import login_required, requires_access_level, ACCESS_ORGANIZER, ACCESS_CLUB_OWNER, ACCESS_HOSTESS, \
    ACCESS_PROMOTER
from models import User, Location, Code, Party, PartyFile, Purchase, Refund
from models.party.constants import NORMAL
from datetime import datetime
from models.configuration import config
from .functions import parties_list, purchases_list
from apis.auth.email import send_activation_email
from utilities import activation_code, datetime_python
from sqlalchemy import or_
import random
from mollie.api.client import Client
from utilities import last_month_datetime, upload_file
from sqlalchemy import func
from flask import request


api = Namespace("organizer", description="Organizer")


@api.route("/config")
class OrganizerAPIConfig(Resource):

    @api.response(200, "Config")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self):
        """Get config"""
        return config().json()

    @api.expect(api.model("Config", {
        "default_club_owner_commission": fields.String(required=True),
        "default_promoter_commission": fields.String(required=True),
        "mollie_api_key": fields.String(required=True),
        "minimum_promoter_commission": fields.Float(required=True),
        "administration_costs": fields.Float(required=True),
        "test_email": fields.String(),
    }), validate=True)
    @api.response(200, "Config")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def post(self):
        """Update config"""
        c = config()
        c.default_club_owner_commission = api.payload["default_club_owner_commission"]
        c.default_promoter_commission = api.payload["default_promoter_commission"]
        c.mollie_api_key = api.payload["mollie_api_key"]
        c.test_email = api.payload["test_email"]
        c.set_minimum_promoter_commission(api.payload["minimum_promoter_commission"])
        c.set_administration_costs(api.payload["administration_costs"])
        db.session.commit()
        return c.json()


@api.route("/create_new_club_owner")
class OrganizerAPICreateClubOwner(Resource):

    @api.expect(api.model("NewClubOwner", {
        "club": fields.String(required=True),
        "email": fields.String(required=True),
        "commission": fields.Integer(required=True),
        "first_name": fields.String(required=True),
    }), validate=True)
    @api.response(200, "Club Owner created")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def post(self):
        """Create new Club Owner account"""
        account = User()
        account.club = api.payload["club"]
        account.email = api.payload["email"]
        account.commission = api.payload["commission"]
        account.commission = api.payload["first_name"]
        account.auth_code = activation_code()
        account.access = ACCESS_CLUB_OWNER
        db.session.add(account)
        db.session.commit()
        send_activation_email(account)
        return


@api.route("/create_new_location")
class OrganizerAPICreateLocation(Resource):

    @api.expect(api.model("NewLocation", {
        "user_id": fields.String(required=True),
        "name": fields.String(required=True),
        "street": fields.String(required=True),
        "street_number": fields.String(required=True),
        "street_number_addition": fields.String(required=True),
        "postal_code": fields.String(required=True),
        "postal_code_letters": fields.String(required=True),
        "city": fields.String(required=True),
        "maps_url": fields.String(),
    }), validate=True)
    @api.response(200, "Location created")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def post(self):
        """Create new Location"""
        club_owner = User.query.filter(User.user_id == api.payload["user_id"]).first()
        location = Location()
        location.user = club_owner
        location.name = api.payload["name"]
        location.street = api.payload["street"]
        location.street_number = api.payload["street_number"]
        location.street_number_addition = api.payload["street_number_addition"]
        location.postal_code = api.payload["postal_code"]
        location.postal_code_letters = api.payload["postal_code_letters"].upper()
        location.city = api.payload["city"]
        location.maps_url = api.payload["maps_url"]
        db.session.add(location)
        db.session.commit()
        return


@api.route("/create_new_hostess")
class OrganizerAPICreateHostess(Resource):

    @api.expect(api.model("NewHostess", {
        "user_id": fields.String(required=True),
        "email": fields.String(required=True),
        "first_name": fields.String(required=True),
        "last_name": fields.String(required=True),
    }), validate=True)
    @api.response(200, "Hostess created")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def post(self):
        """Create new hostess"""
        club_owner = User.query.filter(User.user_id == api.payload["user_id"]).first()
        account = User()
        account.email = api.payload["email"]
        account.first_name = api.payload["first_name"]
        account.last_name = api.payload["last_name"]
        account.auth_code = activation_code()
        account.access = ACCESS_HOSTESS
        account.working = True
        account.club_owner = club_owner
        db.session.add(account)
        db.session.commit()
        send_activation_email(account)
        return


@api.route("/create_new_promoter")
class OrganizerAPICreateHostess(Resource):

    @api.expect(api.model("NewPromoter", {
        "email": fields.String(required=True),
        "first_name": fields.String(required=True),
        "last_name": fields.String(required=True),
        "commission": fields.Integer(required=True),
        "code_id": fields.String(required=True),
    }), validate=True)
    @api.response(200, "Promoter created")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def post(self):
        """Create new promoter"""
        account = User()
        account.email = api.payload["email"]
        account.first_name = api.payload["first_name"]
        account.last_name = api.payload["last_name"]
        account.commission = api.payload["commission"]
        account.code = Code.query.filter(Code.code_id == api.payload["code_id"]).first()
        account.auth_code = activation_code()
        account.access = ACCESS_PROMOTER
        db.session.add(account)
        db.session.commit()
        send_activation_email(account)
        return


@api.route("/update_user_commission")
class OrganizerAPIUpdateUserCommission(Resource):

    @api.expect(api.model("UpdateUserCommission", {
        "user_id": fields.String(required=True),
        "commission": fields.Integer(required=True),
    }), validate=True)
    @api.response(200, "User commission updated")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def patch(self):
        """Update the commission of a user (club owner or promoter)"""
        account = User.query.filter(User.user_id == api.payload["user_id"]).first()
        account.commission = api.payload["commission"]
        db.session.commit()
        return


@api.route("/users")
class OrganizerAPIUsers(Resource):

    @api.response(200, "Users")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self):
        """List of all club owners and promoters"""
        u = User.query.filter(or_(User.access == ACCESS_CLUB_OWNER, User.access == ACCESS_PROMOTER)).all()
        return [user.json() for user in u]


@api.route("/club_owners")
class OrganizerAPIClubOwners(Resource):

    @api.response(200, "Users")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self):
        """List of all club owners"""
        u = User.query.filter(User.access == ACCESS_CLUB_OWNER).all()
        return [user.json() for user in u]


@api.route("/promoters")
class OrganizerAPIPromoters(Resource):

    @api.response(200, "Users")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self):
        """List of all promoters"""
        u = User.query.filter(User.access == ACCESS_PROMOTER).all()
        return [user.json() for user in u]


@api.route("/codes/active")
class OrganizerAPICodesActive(Resource):

    @api.response(200, "Codes")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self):
        """List of all active codes"""
        codes = Code.query.filter(Code.active.is_(True)).order_by(Code.code).all()
        return [c.json() for c in codes]


@api.route("/codes/inactive")
class OrganizerAPICodesInactive(Resource):

    @api.response(200, "Codes")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self):
        """List of all inactive codes"""
        codes = Code.query.filter(Code.active.is_(False)).order_by(Code.code).all()
        return [c.json() for c in codes]


@api.route("/codes")
class OrganizerAPICodes(Resource):

    @api.expect(api.model("Codes", {
        "num": fields.Integer(required=True),
    }), validate=True)
    @api.response(200, "Codes created")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def post(self):
        """Create a number of random codes"""
        all_codes = [f"{n:06}" for n in range(1, 1000000)]
        existing_codes = db.session.query(Code.code).all()
        remaining_codes = list(set(all_codes) - set(existing_codes))
        new_codes = random.sample(remaining_codes, api.payload["num"])
        for code in new_codes:
            c = Code()
            c.code = code
            db.session.add(c)
        db.session.commit()
        return


@api.route("/assign_code_to_promoter")
class OrganizerAPIAssignCodeToPromoter(Resource):

    @api.expect(api.model("UserCode", {
        "user_id": fields.String(required=True),
        "code_id": fields.String(required=True),
    }), validate=True)
    @api.response(200, "Code assigned")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def patch(self):
        """Assign code to Promoter"""
        account = User.query.filter(User.user_id == api.payload["user_id"]).first()
        c = Code.query.filter(Code.code_id == api.payload["code_id"]).first()
        account.code = c
        db.session.commit()
        return


@api.route("/codes/deactivate/<int:code_id>")
class OrganizerAPICodesDeactivate(Resource):

    @api.expect(api.model("UserCode", {
        "user_id": fields.String(required=True),
        "code_id": fields.String(required=True),
    }), validate=True)
    @api.response(200, "Code deactivated")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def patch(self, code_id):
        """Deactivate a code"""
        code = Code.query.filter(Code.code_id == code_id).first()
        code.deactivate()
        db.session.commit()
        return


@api.route("/create_new_party")
class OrganizerAPICreateNewParty(Resource):

    @api.expect(api.model("CreateNewParty", {
        "club": fields.String(required=True),
        "name": fields.String(required=True),
        "location": fields.String(required=True),
        "start_date": fields.String(required=True),
        "end_date": fields.String(required=True),
        "description": fields.String(),
        "number_of_tickets": fields.Integer(required=True),
        "ticket_price": fields.Float(required=True),
        "club_owner_commission": fields.Integer(required=True),
        "promoter_commission": fields.Integer(required=True),
        "images": fields.List(fields.Integer(required=True)),
        "logo": fields.String(required=True),
        "interval": fields.Integer(required=True),
    }), validate=True)
    @api.response(200, "Code deactivated")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def post(self):
        """Create new party"""
        club_owner = User.query.filter(User.user_id == api.payload["club"]).first()
        party = Party()
        party.name = api.payload["name"]
        party.location_id = api.payload["location"]
        party.party_start_datetime = datetime_python(api.payload["start_date"])
        party.party_end_datetime = datetime_python(api.payload["end_date"])
        if "description" in api.payload:
            party.description = api.payload["description"]
        party.num_available_tickets = api.payload["number_of_tickets"]
        party.set_ticket_price(api.payload["ticket_price"])
        party.status = NORMAL
        party.club_owner_commission = api.payload["club_owner_commission"]
        party.club_owner = club_owner
        party.promoter_commission = api.payload["promoter_commission"]
        for idx, file_id in enumerate(api.payload["images"]):
            party_file = PartyFile()
            party_file.party = party
            party_file.file_id = file_id
            party_file.order = idx
        party.logo_id = api.payload["logo"]
        party.interval = api.payload["interval"]
        db.session.add(party)
        db.session.commit()
        return


@api.route("/edit_party/<int:party_id>")
class OrganizerAPIEditParty(Resource):

    @api.expect(api.model("CreateNewParty", {
        "name": fields.String(required=True),
        "number_of_tickets": fields.Integer(required=True),
        "ticket_price": fields.Float(required=True),
        "club_owner_commission": fields.Integer(required=True),
        "promoter_commission": fields.Integer(required=True),
    }), validate=True)
    @api.response(200, "Party updated")
    @api.response(404, "Party not found")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def post(self, party_id):
        """Edit party"""
        party = Party.query.filter(Party.party_id == party_id).first()
        if party:
            party.name = api.payload["name"]
            party.num_available_tickets = api.payload["number_of_tickets"]
            party.set_ticket_price(api.payload["ticket_price"])
            party.club_owner_commission = api.payload["club_owner_commission"]
            party.promoter_commission = api.payload["promoter_commission"]
            db.session.commit()
            return
        return abort(404)


@api.route("/inactive_parties")
class OrganizerAPIInactiveParties(Resource):

    @api.response(200, "Parties")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self):
        """List of all inactive parties"""
        parties = Party.query.filter(Party.is_active.is_(False), Party.party_end_datetime > datetime.utcnow())\
            .order_by(Party.party_start_datetime).all()
        return [p.json() for p in parties]


@api.route("/activate_party/<int:party_id>")
class OrganizerAPIActivateParty(Resource):

    @api.response(200, "Party activated")
    @api.response(404, "Party not found")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def patch(self, party_id):
        """Activate party"""
        party = Party.query.filter(Party.party_id == party_id).first()
        if party:
            party.is_active = True
            db.session.commit()
            return
        return abort(404)


@api.route("/deactivate_party/<int:party_id>")
class OrganizerAPIDeactivateParty(Resource):

    @api.response(200, "Party deactivated")
    @api.response(404, "Party not found")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def patch(self, party_id):
        """Deactivate party"""
        party = Party.query.filter(Party.party_id == party_id).first()
        if party:
            party.is_active = False
            db.session.commit()
            return
        return abort(404)


@api.route("/past_parties")
class OrganizerAPIPastParties(Resource):

    @api.response(200, "Parties")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self):
        """List of all past parties"""
        parties = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime < datetime.utcnow()) \
            .order_by(Party.party_start_datetime).all()
        return [p.json() for p in parties]


@api.route("/party_income/<int:year>/<int:month>")
class OrganizerAPIPartyIncome(Resource):

    @api.response(200, "Parties")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self, year, month):
        """List of all parties for a given month"""
        return parties_list(year, month)


@api.route("/purchase/<int:year>/<int:month>")
class OrganizerAPIPurchase(Resource):

    @api.response(200, "Purchases")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self, year, month):
        """List of all purchases for a given month"""
        return purchases_list(year, month)


@api.route("/refund")
class OrganizerAPIRefund(Resource):

    @api.expect(api.model("Refund", {
        "purchase_id": fields.String(required=True),
        "amount": fields.Float(required=True),
    }), validate=True)
    @api.response(200, "Refund given")
    @api.response(400, "Payment could not be refunded")
    @api.response(404, "Payment not found")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def post(self):
        """Give refund from a purchase"""
        mollie_client = Client()
        mollie_client.set_api_key(config().mollie)

        purchase_id = api.payload["purchase_id"]
        amount = api.payload["amount"]
        mollie_value = "{:,.2f}".format(float(amount))

        purchase = Purchase.query.filter(Purchase.purchase_id == purchase_id).first()
        mollie_id = purchase.mollie_payment_id
        payment = mollie_client.payments.get(mollie_id)

        if payment is not None:
            ref = Refund()
            ref.set_price(float(mollie_value))
            ref.purchase = purchase
            db.session.add(ref)
            db.session.commit()

            if payment.can_be_refunded() and 1.0 <= float(amount) <= float(payment.amount_remaining["value"]):
                data = {
                    "amount": {"value": mollie_value, "currency": "EUR"},
                    "description": f"test {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
                }
                r = mollie_client.payment_refunds.with_parent_id(mollie_id).create(data)
                ref.mollie_refund_id = r["id"]
                db.session.commit()
                return purchase.json()
            else:
                db.session.delete(ref)
                db.session.commit()
                return abort(400)
        return abort(404)


@api.route("/commissions/<int:year>/<int:month>")
class OrganizerAPICommissions(Resource):

    @api.response(200, "Commissions")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self, year, month):
        """List of commissions for a given month for all users"""
        last_month = last_month_datetime(year, month)
        purchase = Purchase.query.filter(Purchase.purchase_datetime < datetime.now(),
                                         func.month(Purchase.purchase_datetime) == func.month(last_month),
                                         func.year(Purchase.purchase_datetime) == func.year(last_month)).all()
        promoters = list(set([p.promoter_id for p in purchase if p.promoter_id is not None]))
        club_owners = list(set([p.party.club_owner_id for p in purchase if p.party.club_owner_id is not None]))
        u = User.query.filter(User.user_id.in_(promoters + club_owners), User.is_active.is_(True)).all()
        return [user.commissions_json(purchase) for user in u]


@api.route("/upload_terms")
class OrganizerAPIUploadTerms(Resource):

    @api.response(200, "Config")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def post(self):
        """Upload terms"""
        files = request.files
        pdf_file = upload_file(files["terms"], current_user)
        c = config()
        if pdf_file:
            c.terms = pdf_file
            db.session.commit()
        return c.json()
