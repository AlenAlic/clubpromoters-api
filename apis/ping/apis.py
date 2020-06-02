from flask_restx import Namespace, Resource


api = Namespace("ping", description="Ping the server")


@api.route("")
class DebugAPI(Resource):

    @api.doc(security=None)
    @api.response(200, "Pinged!")
    def get(self):
        """Ping the api"""
        return
