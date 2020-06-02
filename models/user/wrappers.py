from functools import wraps
from flask_login import current_user
from http import HTTPStatus


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous:
            return "", HTTPStatus.UNAUTHORIZED.value
        return f(*args, **kwargs)
    return decorated_function


def requires_access_level(*access_levels):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.access not in access_levels:
                return "", HTTPStatus.FORBIDDEN.value
            return f(*args, **kwargs)
        return decorated_function
    return decorator
