from flask_restx import Namespace, Resource, abort, fields
from models import Party, Code
from datetime import datetime, timedelta
from models.configuration import config


api = Namespace("public", description="Ping the server")


@api.route("/party/<int:party_id>")
class PublicAPIParty(Resource):

    @api.doc(security=None)
    @api.response(200, "Party")
    @api.response(404, "Party not found")
    def get(self, party_id):
        """Get party"""
        p = Party.query.filter(Party.is_active.is_(True), Party.party_start_datetime > datetime.utcnow(),
                               Party.party_id == party_id).first()
        if p:
            return {
                "party": p.json(),
                "settings": config().json(),
            }
        return abort(404)


@api.route("/active_parties")
class PublicAPIActiveParties(Resource):

    @api.doc(security=None)
    @api.response(200, "Active parties")
    def get(self):
        """Get active parties"""
        parties = Party.query.filter(Party.is_active.is_(True),
                                     Party.party_start_datetime > datetime.utcnow()) \
            .order_by(Party.party_start_datetime).all()
        parties = [p for p in parties if p.party_start_datetime - timedelta(hours=1) > datetime.utcnow()]
        return [p.json() for p in parties]


@api.route("/homepage_parties")
class PublicAPIHomepageParties(Resource):

    @api.doc(security=None)
    @api.response(200, "Homepage parties")
    def get(self):
        """Get homepage parties (all parties of the next available day)"""
        parties = Party.query.filter(Party.is_active.is_(True),
                                     Party.party_start_datetime > datetime.utcnow()) \
            .order_by(Party.party_start_datetime, Party.party_id).all()
        parties = [p for p in parties if p.party_start_datetime - timedelta(hours=1) > datetime.utcnow()]
        if len(parties) == 0:
            return []
        min_date = min([p.party_start_datetime for p in parties])
        parties = [p for p in parties if p.party_start_datetime == min_date]
        return [p.json() for p in parties]


@api.route("/check_code")
class PublicAPICheckCode(Resource):

    @api.doc(security=None)
    @api.expect(api.model("Code", {
        "code": fields.String(required=True),
    }), validate=True)
    @api.response(200, "Code verified")
    @api.response(400, "Bad code")
    def post(self):
        """Check code"""
        code = Code.query.filter(Code.active.is_(True), Code.code == api.payload["code"]).first()
        if code:
            return
        return abort(400)
