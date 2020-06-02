from flask_restx import Namespace, Resource, fields
from flask_login import current_user
from ext import db
from models import login_required, requires_access_level, ACCESS_CLUB_OWNER, ACCESS_HOSTESS
from models import User, Party
from apis.auth.email import send_activation_email
from utilities import activation_code
from datetime import datetime
from .functions import parties_list


api = Namespace("club_owner", description="Club Owner")


@api.route("/create_new_hostess")
class ClubOwnerAPICreateNewHostess(Resource):

    @api.expect(api.model("CreateNewHostess", {
        "email": fields.String(required=True),
        "first_name": fields.String(required=True),
        "last_name": fields.String(required=True),
    }), validate=True)
    @api.response(200, "Account created")
    @login_required
    @requires_access_level(ACCESS_CLUB_OWNER)
    def post(self):
        """Create new hostess account"""
        account = User()
        account.email = api.payload["email"]
        account.first_name = api.payload["first_name"]
        account.last_name = api.payload["last_name"]
        account.auth_code = activation_code()
        account.access = ACCESS_HOSTESS
        account.working = True
        account.club_owner = current_user
        send_activation_email(account)
        db.session.add(account)
        db.session.commit()
        send_activation_email(account)
        return


@api.route("/hostesses")
class ClubOwnerAPIHostesses(Resource):

    @api.response(200, "List of hostesses")
    @login_required
    @requires_access_level(ACCESS_CLUB_OWNER)
    def get(self):
        """Get list of hostesses"""
        usr = User.query.filter(User.access == ACCESS_HOSTESS, User.club_owner_id == current_user.user_id).all()
        return [user.json() for user in usr]


@api.route("/activate_hostess/<int:hostess_id>")
class ClubOwnerAPIActivateHostess(Resource):

    @api.expect(api.model("CreateNewHostess", {
        "working": fields.Boolean(required=True),
    }), validate=True)
    @api.response(200, "Hostess (de)activated")
    @login_required
    @requires_access_level(ACCESS_CLUB_OWNER)
    def patch(self, hostess_id):
        """Create new hostess account"""
        hostess = User.query.filter(User.user_id == hostess_id).first()
        hostess.working = api.payload["working"]
        db.session.commit()
        return


@api.route("/inactive_parties")
class ClubOwnerAPIInactiveParties(Resource):

    @api.response(200, "Inactive parties")
    @login_required
    @requires_access_level(ACCESS_CLUB_OWNER)
    def get(self):
        """Get list of inactive parties"""
        parties = Party.query.filter(Party.is_active.is_(False), Party.party_end_datetime > datetime.utcnow(),
                                     Party.club_owner == current_user).order_by(Party.party_start_datetime).all()
        return [p.json() for p in parties]


@api.route("/active_parties")
class ClubOwnerAPIActiveParties(Resource):

    @api.response(200, "Active parties")
    @login_required
    @requires_access_level(ACCESS_CLUB_OWNER)
    def get(self):
        """Get list of active parties"""
        parties = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime > datetime.utcnow(),
                                     Party.club_owner == current_user).order_by(Party.party_start_datetime).all()
        return [p.json() for p in parties]


@api.route("/past_parties")
class ClubOwnerAPIPastParties(Resource):

    @api.response(200, "Past parties")
    @login_required
    @requires_access_level(ACCESS_CLUB_OWNER)
    def get(self):
        """Get list of past parties"""
        parties = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime < datetime.utcnow(),
                                     Party.club_owner == current_user).order_by(Party.party_start_datetime).all()
        return [p.json() for p in parties]


@api.route("/party_income/<int:year>/<int:month>")
class ClubOwnerAPIPartyIncome(Resource):

    @api.response(200, "Past parties")
    @login_required
    @requires_access_level(ACCESS_CLUB_OWNER)
    def get(self, year, month):
        """Get list of parties of a specific month"""
        return parties_list(year, month)
