from functools import wraps
from flask import request
from http import HTTPStatus
from models import get_code_from_request


def code_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_code_from_request(request):
            return "", HTTPStatus.PRECONDITION_REQUIRED.value
        return f(*args, **kwargs)
    return decorated_function
