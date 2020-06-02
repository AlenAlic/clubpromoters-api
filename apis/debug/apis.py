from flask_restx import Namespace, Resource
from models import login_required


api = Namespace("debug", description="Endpoints useful for debugging and/or testing")


@api.route("/ping")
class DebugAPI(Resource):

    @login_required
    @api.response(200, "Debug pinged!")
    def get(self):
        """Ping the debug api"""
        return
