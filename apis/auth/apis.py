from flask_restx import Namespace, Resource, abort, fields
from flask import jsonify, request
from flask_login import current_user, logout_user
from constants import SECONDS_MONTH, SECONDS_DAY
from ext import db
from models import User
from models import get_token_from_request
from models import login_required
from .functions import check_password_requirements
from .email import send_password_reset_email, send_password_changed_email


api = Namespace("auth", description="Authentication")


@api.route("/login")
class AuthAPILogin(Resource):

    @api.doc(security=None)
    @api.expect(api.model("Login", {
        "email": fields.String(required=True),
        "password": fields.String(required=True),
        "remember_me": fields.Boolean(default=False),
    }), validate=True)
    @api.response(200, "Token")
    @api.response(401, "Username or password incorrect")
    @api.response(403, "Account inactive")
    def post(self):
        """Get authentication token"""
        u = User.query.filter(User.email == api.payload["email"]).first()
        if u is None or not u.check_password(api.payload["password"]):
            abort(401)
        elif u.is_active:
            return jsonify(u.get_auth_token(expires_in=SECONDS_MONTH if api.payload["remember_me"] else SECONDS_DAY))
        return abort(403)


@api.route("/renew")
class AuthAPIRenew(Resource):

    @api.response(200, "Token")
    @api.response(401, "Token expired")
    @login_required
    def get(self):
        """Renew authentication token"""
        data = get_token_from_request(request)
        if data is not None:
            return jsonify(current_user.get_auth_token(expires_in=int(data["exp"] - data["iat"])))
        return abort(401)


@api.route("/logout")
class AuthAPILogout(Resource):

    @api.response(200, "Logged out")
    @login_required
    def delete(self):
        """Log out"""
        logout_user()
        return


@api.route("/activate/<string:token>")
class AuthAPIActivate(Resource):

    @api.doc(security=None)
    @api.expect(api.model("Activate", {
        "password": fields.String(required=True),
        "repeat_password": fields.String(required=True),
    }), validate=True)
    @api.response(200, "Account activated")
    @api.response(400, "Token invalid")
    def post(self, token):
        """Activate an user account"""
        u = User.query.filter(User.auth_code == token).first()
        if u is not None:
            if check_password_requirements(api.payload["password"], api.payload["repeat_password"]):
                u.set_password(api.payload["password"])
                u.auth_code = None
                u.is_active = True
                db.session.commit()
                return
        return abort(400)


@api.route("/password/reset")
class AuthAPIResetPasswordRequest(Resource):

    @api.doc(security=None)
    @api.expect(api.model("ResetPasswordRequest", {
        "email": fields.String(required=True),
    }), validate=True)
    @api.response(200, "Request received")
    def post(self):
        """
        Request new password.

        Will always return HTTP status 200, and only send an email if an account with a matching email is found.
        """
        u = User.query.filter(User.email.ilike(api.payload["email"])).first()
        if u is not None:
            send_password_reset_email(u)
        return


@api.route("/password/reset/<string:token>")
class AuthAPIResetPassword(Resource):

    @api.doc(security=None)
    @api.expect(api.model("ResetPassword", {
        "password": fields.String(required=True),
        "repeat_password": fields.String(required=True),
    }), validate=True)
    @api.response(200, "Password successfully reset")
    @api.response(400, "Password requirements not met")
    @api.response(401, "Token invalid")
    def post(self, token):
        """Reset password"""
        u = User.verify_reset_password_token(token)
        if u is not None:
            if check_password_requirements(api.payload["password"], api.payload["repeat_password"]):
                u.set_password(api.payload["password"])
                db.session.commit()
                return
            return abort(400)
        return abort(401)


@api.route("/password/change")
class AuthAPIChangePassword(Resource):

    @api.expect(api.model("ChangePassword", {
        "password": fields.String(required=True),
        "new_password": fields.String(required=True),
        "repeat_password": fields.String(required=True),
    }), validate=True)
    @api.response(200, "Password successfully changed")
    @api.response(400, "Password requirements not met")
    @api.response(403, "Current password incorrect")
    @login_required
    def patch(self,):
        """Change password"""
        if current_user.check_password(api.payload["password"]):
            if check_password_requirements(api.payload["new_password"], api.payload["repeat_password"]) \
                    and api.payload["new_password"] != api.payload["password"]:
                current_user.set_password(api.payload["new_password"], increment=True)
                db.session.commit()
                send_password_changed_email()
                return
            return abort(400)
        return abort(403)
