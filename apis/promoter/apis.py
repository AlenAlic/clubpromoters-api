from flask_restx import Namespace, Resource
from flask_login import current_user
from models import login_required, requires_access_level, ACCESS_PROMOTER
from utilities import last_month_datetime


api = Namespace("promoter", description="Promoter")


@api.route("/code")
class PromoterAPICode(Resource):

    @api.response(200, "Code")
    @login_required
    @requires_access_level(ACCESS_PROMOTER)
    def get(self):
        """Get promoter code"""
        return current_user.code.json() if current_user.code else None


@api.route("/income/<int:year>/<int:month>")
class PromoterAPIIncome(Resource):

    @api.response(200, "Income")
    @login_required
    @requires_access_level(ACCESS_PROMOTER)
    def get(self, year, month):
        """Get promoter income of a given year and month"""
        return current_user.promoter_income(last_month_datetime(year, month))
