from flask_restx import Namespace, Resource, abort
from models import Code


api = Namespace("code", description="Code")


@api.route("/<int:code_id>/image")
class MollieAPIWebhook(Resource):

    @api.doc(security=None)
    @api.response(200, "Base64 string")
    @api.response(404, "Code not found")
    def get(self, code_id):
        """Get .png base64 encoded image"""
        code = Code.query.filter(Code.code_id == code_id).first()
        if code:
            return code.qr_code()
        return abort(404)
