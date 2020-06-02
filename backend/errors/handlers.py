from flask import render_template, request, jsonify
from ext import db
from backend.errors import bp
from .email import send_error_email
import traceback
from http import HTTPStatus


def wants_json_response():
    return request.accept_mimetypes["application/json"] >= request.accept_mimetypes["text/html"]


def json_error(status_code):
    payload = {"error": status_code}
    response = jsonify(payload)
    response.status_code = status_code
    return response


@bp.app_errorhandler(404)
def not_found_error(error):
    if wants_json_response():
        return json_error(HTTPStatus.NOT_FOUND.value)
    return render_template("errors/404.html", error=error)


@bp.app_errorhandler(Exception)
def handle_unexpected_error(error):
    db.session.rollback()
    trace = traceback.format_exc()
    trace = trace.split("\n")
    trace = [t for t in trace if len(t) > 0]
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
    send_error_email(status_code, error, trace)
    if wants_json_response():
        return json_error(status_code)
    return render_template("errors/500.html", status_code=status_code, error=error, trace=trace)
