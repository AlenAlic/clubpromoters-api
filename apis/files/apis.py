from flask_restx import Namespace, Resource, abort, fields
from ext import db
from models import login_required, requires_access_level, ACCESS_ORGANIZER, ACCESS_CLUB_OWNER
from models import File


api = Namespace("files", description="Files")


@api.route("/<int:file_id>")
class DocumentsAPIInvoice(Resource):

    @api.expect(api.model("File", {
        "name": fields.String(required=True),
    }), validate=True)
    @api.response(200, "File")
    @api.response(404, "File not found")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER, ACCESS_CLUB_OWNER)
    def patch(self, file_id):
        """Terms and conditions"""
        file = File.query.filter(File.file_id == file_id).first()
        if file:
            file.name = api.payload["name"]
            db.session.commit()
            return
        return abort(404)

    @api.response(200, "File")
    @api.response(404, "File not found")
    @api.response(409, "File cannot be deleted")
    @login_required
    @requires_access_level(ACCESS_ORGANIZER, ACCESS_CLUB_OWNER)
    def delete(self, file_id):
        """Terms and conditions"""
        file = File.query.filter(File.file_id == file_id).first()
        if file:
            if file.deletable:
                db.session.delete(file)
                db.session.commit()
                file.remove_from_disk()
                return
            return abort(409)
        return abort(404)
