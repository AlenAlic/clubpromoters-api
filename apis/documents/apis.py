from flask_restx import Namespace, Resource, abort
from flask import send_from_directory
from models.configuration import config


api = Namespace("documents", description="Website documents")


@api.route("/terms")
class DocumentsAPITerms(Resource):

    @api.doc(security=None)
    @api.response(200, "Terms and conditions (as shown at checkout)")
    @api.response(404, "Terms and conditions not found")
    def get(self):
        """Terms and conditions"""
        file = config().terms
        if file:
            return send_from_directory(file.directory, filename=file.filename, cache_timeout=0)
        return abort(404)
