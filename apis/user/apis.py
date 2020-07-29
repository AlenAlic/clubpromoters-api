from flask_restx import Namespace, Resource, abort, fields
from flask_login import current_user
from flask import request
from ext import db
from models import login_required, requires_access_level
from models import User
from models.user.constants import ACCESS_ORGANIZER, ACCESS_CLUB_OWNER, ACCESS_PROMOTER
from utilities import upload_image
from constants import VUE_LANGUAGES, VUE_ENGLISH
from models.invoice.constants import INVOICE_LANGUAGES, DUTCH
from utilities import activation_code
from apis.auth.email import send_activation_email


api = Namespace("user", description="User")


profile = api.model("ProfileResponse", {
    "id": fields.Integer,
    "email": fields.String,
    "first_name": fields.String,
    "last_name": fields.String,
    "full_name": fields.String,
    "street": fields.String,
    "street_number": fields.Integer,
    "street_number_addition": fields.String,
    "postal_code": fields.Integer,
    "postal_code_letters": fields.String,
    "city": fields.String,
    "country": fields.String,
    "phone_number": fields.String,
})


@api.route("/profile")
class UserAPIProfile(Resource):

    @api.response(200, "Profile", profile)
    @login_required
    def get(self):
        """Get user profile"""
        return current_user.profile

    @api.expect(api.model("Profile", {
        "first_name": fields.String(required=True),
        "last_name": fields.String(required=True),
        "phone_number": fields.String(),
    }), validate=True)
    @api.response(200, "Profile", profile)
    @login_required
    def patch(self):
        """Update user profile"""
        current_user.first_name = api.payload["first_name"]
        current_user.last_name = api.payload["last_name"]
        current_user.phone_number = api.payload["phone_number"]
        db.session.commit()
        return current_user.profile


@api.route("/register")
class Register(Resource):

    @api.doc(security=None)
    @api.expect(api.model("Register", {
        "email": fields.String(required=True),
        "first_name": fields.String(required=True),
        "last_name": fields.String(required=True),
        "terms": fields.Boolean(required=True),
        "type": fields.Integer(default=ACCESS_PROMOTER),
    }), validate=True)
    @api.response(200, "Registered")
    @api.response(400, "Not accepted terms")
    @api.response(409, "E-mail address taken")
    def post(self):
        """Register a new User"""
        if api.payload["terms"]:
            email = api.payload["email"]
            user = User.query.filter(User.email.ilike(email)).first()
            if not user:
                account = User()
                account.email = email
                account.first_name = api.payload["first_name"]
                account.last_name = api.payload["last_name"]
                account.auth_code = activation_code()
                account.access = api.payload["type"]
                account.accepted_terms = True
                db.session.add(account)
                db.session.commit()
                send_activation_email(account)
                return
            return abort(409)
        return abort(400)


@api.route("/address")
class UserAPIAddress(Resource):

    @api.expect(api.model("Address", {
        "street": fields.String(required=True),
        "street_number": fields.Integer(required=True),
        "street_number_addition": fields.String(required=True),
        "postal_code": fields.Integer(required=True),
        "postal_code_letters": fields.String(required=True),
        "city": fields.String(required=True),
        "country": fields.String(required=True),
    }), validate=True)
    @api.response(200, "Profile", profile)
    @login_required
    def patch(self):
        """Update user address"""
        current_user.street = api.payload["street"]
        current_user.street_number = api.payload["street_number"]
        current_user.street_number_addition = api.payload["street_number_addition"]
        current_user.postal_code = api.payload["postal_code"]
        current_user.postal_code_letters = api.payload["postal_code_letters"]
        current_user.city = api.payload["city"]
        current_user.country = api.payload["country"]
        db.session.commit()
        return current_user.profile


@api.route("/language")
class UserAPIAddress(Resource):

    @api.expect(api.model("Language", {
        "language": fields.String(required=True),
    }), validate=True)
    @api.response(200, "Profile", profile)
    @login_required
    def patch(self):
        """Update user language preference"""
        if api.payload["language"] in VUE_LANGUAGES:
            current_user.language = api.payload["language"]
        else:
            current_user.language = VUE_ENGLISH
        db.session.commit()
        return current_user.profile


@api.route("/invoice_data")
class UserAPIAddress(Resource):

    @api.expect(api.model("InvoiceData", {
        "legal_name": fields.String(required=True),
        "iban": fields.String(required=True),
        "kvk_number": fields.String(),
        "vat_number": fields.String(),
    }), validate=True)
    @api.response(200, "Profile", profile)
    @login_required
    def patch(self):
        """Update user invoice data"""
        current_user.invoice_legal_name = api.payload["legal_name"]
        current_user.iban = api.payload["iban"]
        if "kvk_number" in api.payload:
            current_user.invoice_kvk_number = api.payload["kvk_number"]
        if "vat_number" in api.payload:
            current_user.invoice_vat_number = api.payload["vat_number"]
        db.session.commit()
        return current_user.profile


@api.route("/invoice_language")
class UserAPIAddress(Resource):

    @api.expect(api.model("InvoiceLanguage", {
        "invoice_language": fields.String(required=True),
    }), validate=True)
    @api.response(200, "Profile", profile)
    @login_required
    def patch(self):
        """Update user language preference"""
        if api.payload["invoice_language"] in INVOICE_LANGUAGES:
            current_user.invoice_language = api.payload["invoice_language"]
        else:
            current_user.invoice_language = DUTCH
        db.session.commit()
        return current_user.profile


@api.route("/assets/<int:user_id>")
class UserAPIAssets(Resource):

    @api.response(200, "Assets")
    @api.response(404, "User not found")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER, ACCESS_CLUB_OWNER)
    def get(self, user_id):
        """Get user assets"""
        user = User.query.filter(User.user_id == user_id).first()
        if user:
            return user.assets()
        return abort(404)


@api.route("/upload/images/<int:user_id>")
class UserAPIProfile(Resource):

    @api.response(200, "Images uploaded")
    @api.response(404, "User not found")
    @login_required
    def post(self, user_id):
        """Upload images"""
        user = User.query.filter(User.user_id == user_id).first()
        if user:
            form = request.form
            files = request.files
            for image in files:
                upload_image(files[image], user, logo=form["logo"] == "true")
            db.session.commit()
            return
        return abort(404)
