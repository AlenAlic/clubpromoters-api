from flask_restx import Namespace, Resource, abort, fields
from flask_login import current_user
from flask import request
from ext import db
from models import login_required, requires_access_level
from models import User
from models.user.constants import ACCESS_ORGANIZER, ACCESS_CLUB_OWNER
from utilities import upload_image


api = Namespace("user", description="User")


profile = api.model("ProfileResponse", {
    "id": fields.Integer,
    "email": fields.String,
    "first_name": fields.String,
    "last_name": fields.String,
    "full_name": fields.String,
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
    }), validate=True)
    @api.response(200, "Profile", profile)
    @login_required
    def patch(self):
        """Update user profile"""
        current_user.first_name = api.payload["first_name"]
        current_user.last_name = api.payload["last_name"]
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
    def patch(self, user_id):
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