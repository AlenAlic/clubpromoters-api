from flask_restx import Namespace, Resource, abort, fields
from ext import db
from models import User
from models import login_required, requires_access_level, ACCESS_ADMIN, ACCESS_ORGANIZER
from .email import send_activation_email
from utilities import activation_code


api = Namespace("admin", description="Admin")


@api.route("/switch")
class AuthAPISwitch(Resource):

    @api.response(200, "User list")
    @login_required
    @requires_access_level(ACCESS_ADMIN)
    def get(self):
        """Get list of users that you can switch to"""
        users = User.query.filter(User.access != ACCESS_ADMIN, User.is_active.is_(True)).all()
        return [{
            "text": u.email,
            "value": u.user_id
        } for u in users]


@api.route("/switch/<int:user_id>")
class AuthAPISwitchUser(Resource):

    @api.response(200, "User created")
    @api.response(400, "Active user not found")
    @login_required
    @requires_access_level(ACCESS_ADMIN)
    def post(self, user_id):
        """Get token to log in as a different user"""
        usr = User.query.filter(User.access != ACCESS_ADMIN, User.is_active.is_(True), User.user_id == user_id).first()
        if usr is not None:
            return usr.get_auth_token()
        return abort(400)


@api.route("/has_organizer")
class AdminAPIHasOrganizer(Resource):

    @api.response(200, "Has organiser account")
    @login_required
    @requires_access_level(ACCESS_ADMIN)
    def get(self):
        """Check if there is an organizer account"""
        users = User.query.filter(User.access == ACCESS_ORGANIZER).count()
        return users > 0


@api.route("/create_organizer_account")
class AdminAPICreateOrganizer(Resource):

    @api.expect(api.model("CreateOrganizer", {
        "email": fields.String(required=True),
        # "first_name": fields.String(required=True),
    }), validate=True)
    @api.response(200, "User created")
    @login_required
    @requires_access_level(ACCESS_ADMIN)
    def post(self):
        """Create organizer account"""
        organizer = User()
        organizer.email = api.payload["email"]
        # organizer.first_name = api.payload["first_name"]
        organizer.access = ACCESS_ORGANIZER
        organizer.auth_code = activation_code()
        db.session.add(organizer)
        db.session.commit()
        send_activation_email(organizer)
        return
