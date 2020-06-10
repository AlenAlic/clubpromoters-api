from flask_restx import Namespace, Resource, fields
from flask_login import current_user
from ext import db
from models import login_required, requires_access_level, ACCESS_CLUB_OWNER, ACCESS_HOSTESS
from models import User, Party
from apis.auth.email import send_activation_email
from utilities import activation_code
from datetime import datetime
from .functions import parties_list
from utilities import cents_to_euro
from sqlalchemy import func


api = Namespace("club_owner", description="Club Owner")


@api.route("/dashboard/graphs")
class OrganizerAPIDashboardGraphs(Resource):

    @api.response(200, "This year's financial data")
    @login_required
    @requires_access_level(ACCESS_CLUB_OWNER)
    def get(self):
        """Get this year's financial data"""
        now = datetime.utcnow()
        parties = Party.query.filter(Party.party_end_datetime < datetime.utcnow(),
                                     func.year(Party.party_end_datetime) == func.year(now)).all()
        months = []
        tickets_sold = []
        commission = []
        for month in range(1, 13):
            months.append(month)
            month_parties = [p for p in parties if p.party_start_datetime.month == month]
            month_tickets_sold = sum([p.income_number_tickets_sold for p in month_parties]
                                     if len(month_parties) else [0])
            month_commission = sum([p.income_club_owner_commission for p in month_parties]
                                   if len(month_parties) else [0])
            tickets_sold.append(month_tickets_sold)
            commission.append(month_commission)
        commission = [cents_to_euro(c) for c in commission]
        return {
            "months": months,
            "tickets_sold": tickets_sold,
            "commission": commission,
        }


@api.route("/dashboard/this_month")
class OrganizerAPIDashboardThisMonth(Resource):

    @api.response(200, "This month's financial data")
    @login_required
    @requires_access_level(ACCESS_CLUB_OWNER)
    def get(self):
        """Get this month's financial data"""
        now = datetime.utcnow()
        parties = Party.query.filter(Party.party_end_datetime < datetime.utcnow(),
                                     func.year(Party.party_end_datetime) == func.year(now),
                                     func.month(Party.party_end_datetime) == func.month(now)).all()
        tickets_sold = sum([p.income_number_tickets_sold for p in parties] if len(parties) else [0])
        commission = sum([p.income_club_owner_commission for p in parties] if len(parties) else [0])
        return {
            "tickets_sold": tickets_sold,
            "commission": cents_to_euro(commission),
        }


@api.route("/dashboard/last_month")
class OrganizerAPIDashboardLastMonth(Resource):

    @api.response(200, "Last month's financial data")
    @login_required
    @requires_access_level(ACCESS_CLUB_OWNER)
    def get(self):
        """Get last month's financial data"""
        now = datetime.utcnow()
        last_month = now.replace(month=now.month - 1 or 12)
        parties = Party.query.filter(Party.party_end_datetime < datetime.utcnow(),
                                     func.year(Party.party_end_datetime) == func.year(now),
                                     func.month(Party.party_end_datetime) == func.month(last_month)).all()
        tickets_sold = sum([p.income_number_tickets_sold for p in parties] if len(parties) else [0])
        commission = sum([p.income_club_owner_commission for p in parties] if len(parties) else [0])
        return {
            "tickets_sold": tickets_sold,
            "commission": cents_to_euro(commission),
        }


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
