from flask import request


def filtered_form():
    return {k: v for k, v in request.form.items() if k not in
            ["csrf_token", "password", "current_password", "new_password", "repeat_password"]}
