from flask_restx import Namespace, Resource, abort, fields
from flask import send_file
from ext import db
from models import login_required, requires_access_level, ACCESS_ORGANIZER, ACCESS_CLUB_OWNER, ACCESS_HOSTESS, \
    ACCESS_PROMOTER
from models import User, Location, Code, Party, PartyFile, Purchase, Refund, Ticket, Invoice
from models.party.constants import NORMAL
from datetime import datetime, timedelta
from models.configuration import config
from .functions import parties_list, purchases_list, commissions, this_months_invoices
from apis.auth.email import send_activation_email
from utilities import activation_code, datetime_python
from sqlalchemy import or_
import random
from mollie.api.client import Client
from utilities import last_month_datetime
from sqlalchemy import func
from utilities import euro_to_cents, cents_to_euro
import xlsxwriter
from io import BytesIO
import pyqrcode
from models.invoice.functions import generate_serial_number
from .constants import DAILY, WEEKLY, BIWEEKLY
from constants import STATUS_PAID
from mollie.api.error import ResponseError


api = Namespace("organizer", description="Organizer")


@api.route("/config")
class OrganizerAPIConfig(Resource):

    @api.response(200, "Config")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self):
        """Get config"""
        return config().json()


@api.route("/dashboard/graph")
class OrganizerAPIDashboardGraphs(Resource):

    @api.response(200, "This year's financial data")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self):
        """Get this year's financial data"""
        now = datetime.utcnow()
        purchases = Purchase.query.filter(Purchase.purchase_datetime < datetime.utcnow(),
                                          Purchase.status == STATUS_PAID,
                                          func.year(Purchase.purchase_datetime) == func.year(now)).all()
        months = []
        revenue = []
        expenses = []
        profit = []
        for month in range(1, now.month + 1):
            months.append(month)
            month_purchases = [p for p in purchases if p.purchase_datetime.month == month]
            month_revenue = sum([p.price + p.administration_costs for p in month_purchases])
            month_expenses = sum([p.refunded_amount + p.expenses_promoter_commissions +
                                  p.expenses_club_owner_commissions for p in month_purchases])
            month_profit = month_revenue - month_expenses
            revenue.append(month_revenue + revenue[-1] if len(revenue) else 0)
            expenses.append(month_expenses + expenses[-1] if len(expenses) else 0)
            profit.append(month_profit + profit[-1] if len(profit) else 0)
        revenue = [cents_to_euro(r) for r in revenue]
        expenses = [cents_to_euro(e) for e in expenses]
        profit = [cents_to_euro(p) for p in profit]
        return {
            "months": months,
            "revenue": revenue,
            "expenses": expenses,
            "profit": profit,
        }


@api.route("/dashboard/this_month")
class OrganizerAPIDashboardThisMonth(Resource):

    @api.response(200, "This month's financial data")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self):
        """Get this month's financial data"""
        now = datetime.utcnow()
        purchases = Purchase.query.filter(Purchase.purchase_datetime < datetime.utcnow(),
                                          Purchase.status == STATUS_PAID,
                                          func.year(Purchase.purchase_datetime) == func.year(now),
                                          func.month(Purchase.purchase_datetime) == func.month(now)).all()
        revenue = sum([p.price + p.administration_costs for p in purchases] if len(purchases) else [0])
        expenses = sum([p.refunded_amount + p.expenses_promoter_commissions +
                        p.expenses_club_owner_commissions for p in purchases] if len(purchases) else [0])
        profit = revenue - expenses
        return {
            "revenue": cents_to_euro(revenue),
            "expenses": cents_to_euro(expenses),
            "profit": cents_to_euro(profit),
        }


@api.route("/dashboard/last_month")
class OrganizerAPIDashboardLastMonth(Resource):

    @api.response(200, "Last month's financial data")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self):
        """Get last month's financial data"""
        now = datetime.utcnow()
        last_month = now.replace(month=now.month - 1 or 12)
        purchases = Purchase.query.filter(Purchase.purchase_datetime < datetime.utcnow(),
                                          Purchase.status == STATUS_PAID,
                                          func.year(Purchase.purchase_datetime) == func.year(now),
                                          func.month(Purchase.purchase_datetime) == func.month(last_month)).all()
        revenue = sum([p.price + p.administration_costs for p in purchases] if len(purchases) else [0])
        expenses = sum([p.refunded_amount + p.expenses_promoter_commissions +
                        p.expenses_club_owner_commissions for p in purchases] if len(purchases) else [0])
        profit = revenue - expenses
        return {
            "revenue": cents_to_euro(revenue),
            "expenses": cents_to_euro(expenses),
            "profit": cents_to_euro(profit),
        }


@api.route("/create_new_club_owner")
class OrganizerAPICreateClubOwner(Resource):

    @api.expect(api.model("NewClubOwner", {
        "club": fields.String(required=True),
        "email": fields.String(required=True),
        "commission": fields.Integer(required=True),
        "first_name": fields.String(required=True),
        "last_name": fields.String(required=True),
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
        account.first_name = api.payload["first_name"]
        account.last_name = api.payload["last_name"]
        account.auth_code = activation_code()
        account.access = ACCESS_CLUB_OWNER
        account.business_entity = True
        db.session.add(account)
        db.session.commit()
        send_activation_email(account)
        return


@api.route("/create_new_location")
class OrganizerAPICreateLocation(Resource):

    @api.expect(api.model("NewLocation", {
        "user_id": fields.Integer(required=True),
        "name": fields.String(required=True),
        "street": fields.String(required=True),
        "street_number": fields.Integer(required=True),
        "street_number_addition": fields.String(required=True),
        "postal_code": fields.Integer(required=True),
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


@api.route("/update_location/<int:location_id>")
class OrganizerAPICreateLocation(Resource):

    @api.expect(api.model("NewLocation", {
        "name": fields.String(required=True),
        "street": fields.String(required=True),
        "street_number": fields.Integer(required=True),
        "street_number_addition": fields.String(required=True),
        "postal_code": fields.Integer(required=True),
        "postal_code_letters": fields.String(required=True),
        "city": fields.String(required=True),
        "maps_url": fields.String(),
    }), validate=True)
    @api.response(200, "Location updated")
    @api.response(200, "Location not found")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def patch(self, location_id):
        """Update existing Location"""
        location = Location.query.filter(Location.location_id == location_id).first()
        if location:
            location.name = api.payload["name"]
            location.street = api.payload["street"]
            location.street_number = api.payload["street_number"]
            location.street_number_addition = api.payload["street_number_addition"]
            location.postal_code = api.payload["postal_code"]
            location.postal_code_letters = api.payload["postal_code_letters"].upper()
            location.city = api.payload["city"]
            location.maps_url = api.payload["maps_url"]
            db.session.commit()
            return
        return abort(404)


@api.route("/create_new_hostess")
class OrganizerAPICreateHostess(Resource):

    @api.expect(api.model("NewHostess", {
        "user_id": fields.Integer(required=True),
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
        "code_id": fields.Integer(),
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
        "user_id": fields.Integer(required=True),
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


@api.route("/codes/excel")
class OrganizerAPICodesExcel(Resource):

    @api.expect(api.model("CodeList", {
        "codes": fields.List(fields.Integer(required=True)),
    }), validate=True)
    @api.response(200, "Excel file containing codes")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def post(self):
        """Excel file containing codes"""
        output = BytesIO()
        wb = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = wb.add_worksheet()
        codes = Code.query.filter(Code.code_id.in_(api.payload["codes"])).order_by(Code.code).all()
        for idx, code in enumerate(codes):
            ws.write(idx, 0, code.code)
            ws.write(idx, 1, code.qr_url)
            buffer = BytesIO()
            img = pyqrcode.create(code.qr_url)
            img.png(buffer, scale=8)
            ws.insert_image(idx, 2, f"{code.code}.png", {"image_data": buffer})
            ws.set_column(0, 0, 20)
            ws.set_column(1, 1, 50)
        wb.close()
        output.seek(0)
        return send_file(output, as_attachment=True, cache_timeout=0,
                         attachment_filename=f"codes_{datetime.utcnow().strftime('%d-%m-%Y_%H%M%S')}.xlsx")


@api.route("/assign_code_to_promoter")
class OrganizerAPIAssignCodeToPromoter(Resource):

    @api.expect(api.model("UserCode", {
        "user_id": fields.Integer(required=True),
        "code_id": fields.Integer(required=True),
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
        "user_id": fields.Integer(required=True),
        "name": fields.String(required=True),
        "location_id": fields.Integer(required=True),
        "start_date": fields.String(required=True),
        "end_date": fields.String(required=True),
        "description": fields.String(),
        "number_of_tickets": fields.Integer(required=True),
        "ticket_price": fields.Float(required=True),
        "club_owner_commission": fields.Integer(required=True),
        "promoter_commission": fields.Integer(required=True),
        "images": fields.List(fields.Integer(required=True)),
        "logo_id": fields.Integer(required=True),
        "interval": fields.Integer(required=True),
        "repeats": fields.Integer(default=1),
        "period": fields.String,
    }), validate=True)
    @api.response(200, "Code deactivated")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def post(self):
        """Create new party"""
        club_owner = User.query.filter(User.user_id == api.payload["user_id"]).first()
        default_start_date = datetime_python(api.payload["start_date"])
        default_end_date = datetime_python(api.payload["end_date"])
        days = 0
        if "period" in api.payload:
            period = api.payload["period"]
            days = 1 if period == DAILY else 7 if period == WEEKLY else 14 if period == BIWEEKLY else 0
        for i in range(api.payload["repeats"]):
            offset = timedelta(days=days) * i
            start_date = default_start_date + offset
            end_date = default_end_date + offset
            party = Party()
            party.name = api.payload["name"]
            party.location_id = api.payload["location_id"]
            party.party_start_datetime = start_date
            party.party_end_datetime = end_date
            if "description" in api.payload:
                party.description = api.payload["description"]
            party.num_available_tickets = api.payload["number_of_tickets"]
            party.ticket_price = euro_to_cents(api.payload["ticket_price"])
            party.status = NORMAL
            party.club_owner_commission = api.payload["club_owner_commission"]
            party.club_owner = club_owner
            party.promoter_commission = api.payload["promoter_commission"]
            for idx, file_id in enumerate(api.payload["images"]):
                party_file = PartyFile()
                party_file.party = party
                party_file.file_id = file_id
                party_file.order = idx
            party.logo_id = api.payload["logo_id"]
            party.interval = api.payload["interval"]
            db.session.add(party)
        db.session.commit()
        return


@api.route("/edit_party/<int:party_id>")
class OrganizerAPIEditParty(Resource):

    @api.expect(api.model("CreateNewParty", {
        "name": fields.String(required=True),
        "description": fields.String(),
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
            party.ticket_price = euro_to_cents(api.payload["ticket_price"])
            party.club_owner_commission = api.payload["club_owner_commission"]
            party.promoter_commission = api.payload["promoter_commission"]
            if "description" in api.payload:
                party.description = api.payload["description"]
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


@api.route("/active_parties")
class OrganizerAPIActiveParties(Resource):

    @api.response(200, "Parties")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self):
        """List of all active parties"""
        parties = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime > datetime.utcnow())\
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
        "purchase_id": fields.Integer(required=True),
        "amount": fields.Float(required=True),
        "tickets": fields.List(fields.Integer(required=True)),
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

        amount = api.payload["amount"]
        mollie_value = "{:,.2f}".format(float(amount))

        purchase = Purchase.query.filter(Purchase.purchase_id == api.payload["purchase_id"]).first()
        mollie_id = purchase.mollie_payment_id
        payment = mollie_client.payments.get(mollie_id)

        if payment is not None:
            if payment.can_be_refunded() and 1.0 <= float(amount) <= float(payment.amount_remaining["value"]):
                ref = Refund()
                ref.price = euro_to_cents(amount)
                ref.purchase = purchase
                tickets = Ticket.query.filter(Ticket.ticket_id.in_(api.payload["tickets"])).all()
                for ticket in tickets:
                    ticket.refunded = True
                data = {
                    "amount": {"value": mollie_value, "currency": "EUR"},
                    "description": f"test {datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')}"
                }
                try:
                    r = mollie_client.payment_refunds.with_parent_id(mollie_id).create(data)
                    ref.mollie_refund_id = r["id"]
                    db.session.add(ref)
                    db.session.commit()
                    # TODO => Add refund receipt
                    return purchase.json()
                except ResponseError:
                    return abort(409)
            else:
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
        return commissions(last_month, filter_users=False)


@api.route("/invoices")
class OrganizerAPIInvoices(Resource):

    @api.response(200, "Users with invoices due for last month")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self):
        """List of commissions for a given month for all users that will receive a payout"""
        now = datetime.utcnow()
        last_month = last_month_datetime(now.year, now.month)
        return {
            "users": commissions(last_month),
            "invoices": [i.json() for i in this_months_invoices(now)],
        }

    @api.expect(api.model("GenerateInvoices", {
        "users": fields.List(fields.Integer(required=True)),
    }), validate=True)
    @api.response(200, "Invoices generated")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def post(self):
        """Generates invoices for a list of users"""
        now = datetime.utcnow()
        last_month = last_month_datetime(now.year, now.month)
        users = User.query.filter(User.user_id.in_(api.payload["users"])).all()
        for user in users:
            parties = user.invoice_parties(last_month)
            serial_number = generate_serial_number(user)
            invoice = Invoice(user, parties, serial_number)
            db.session.add(invoice)
            db.session.flush()
            invoice.generate_invoice()
        db.session.commit()
        return {
            "users": commissions(last_month),
            "invoices": [i.json() for i in this_months_invoices(now)],
        }


@api.route("/invoices/send")
class OrganizerAPIInvoicesSend(Resource):

    @api.expect(api.model("SendInvoices", {
        "invoices": fields.List(fields.Integer(required=True)),
    }), validate=True)
    @api.response(200, "Invoices sent")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def post(self):
        """Send invoices"""
        now = datetime.utcnow()
        last_month = last_month_datetime(now.year, now.month)
        invoices = Invoice.query.filter(Invoice.invoice_id.in_(api.payload["invoices"]), Invoice.sent.is_(False)).all()
        for invoice in invoices:
            invoice.send()
        db.session.commit()
        return {
            "users": commissions(last_month),
            "invoices": [i.json() for i in this_months_invoices(now)],
        }


@api.route("/invoices/all")
class OrganizerAPIInvoicesAll(Resource):

    @api.response(200, "All invoices")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER)
    def get(self):
        """All invoices"""
        return [i.json() for i in Invoice.query.all()]
