from flask import render_template, request, send_from_directory, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from backend.settings import bp
from models import requires_access_level
from models.user.constants import ACCESS_ADMIN, ACCESS_ORGANIZER
from constants import *
from .forms import SettingsForm, TermsForm, RemoveTermsForm
from models.configuration import config
from ext import db
from utilities import upload_file


@bp.route("/", methods=[GET, POST])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def index():
    conf = config()
    settings_form = SettingsForm()
    terms_form = TermsForm()
    remove_terms_form = RemoveTermsForm()
    if request.method == POST:
        if settings_form.save_settings.name in request.form and settings_form.validate_on_submit():
            settings_form.save()
            flash("Settings saved.")
            db.session.commit()
            return redirect(url_for("settings.index"))
        if terms_form.upload_terms.name in request.form and terms_form.validate_on_submit():
            pdf_file = upload_file(terms_form.terms.data, current_user)
            if pdf_file:
                conf.terms = pdf_file
                db.session.commit()
            return redirect(url_for("settings.index"))
        if remove_terms_form.remove_terms.name in request.form:
            conf.terms_id = None
            db.session.commit()
            return redirect(url_for("settings.index"))
    return render_template("settings/index.html", settings_form=settings_form, terms_form=terms_form,
                           remove_terms_form=remove_terms_form, conf=conf)


@bp.route("/terms", methods=[GET, POST])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def terms():
    file = config().terms
    if file:
        return send_from_directory(file.directory, filename=file.filename, as_attachment=True, cache_timeout=0)
    return abort(404)
