from flask import render_template, request, current_app, send_from_directory, flash, redirect, url_for
from flask_login import login_required
from backend.settings import bp
from models import requires_access_level
from models.user.constants import ACCESS_ADMIN, ACCESS_ORGANIZER
from constants import *
from .forms import SettingsForm
from models.configuration import config
from ext import db


@bp.route("/", methods=[GET, POST])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def index():
    conf = config()
    settings_form = SettingsForm()
    if request.method == POST:
        if settings_form.save_settings.name in request.form and settings_form.validate_on_submit():
            settings_form.save()
            flash("Settings saved.")
            db.session.commit()
            return redirect(url_for("settings.index"))
    return render_template("settings/index.html", settings_form=settings_form)
