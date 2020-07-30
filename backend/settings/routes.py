from flask import render_template, request, send_from_directory, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from backend.settings import bp
from models import requires_access_level
from models.user.constants import ACCESS_ADMIN, ACCESS_ORGANIZER
from constants import *
from .forms import SettingsForm, TermsForm, RemoveTermsForm, PromoterTermsForm, RemovePromoterTermsForm
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
    promoter_terms_form = PromoterTermsForm()
    remove_promoter_terms_form = RemovePromoterTermsForm()
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
                flash("New terms uploaded.")
            return redirect(url_for("settings.index"))
        if remove_terms_form.remove_terms.name in request.form:
            conf.terms_id = None
            db.session.commit()
            flash("Terms removed. There are no terms available for customers to view.", "warning")
            return redirect(url_for("settings.index"))
        if promoter_terms_form.promoter_upload_terms.name in request.form and promoter_terms_form.validate_on_submit():
            pdf_file = upload_file(promoter_terms_form.promoter_terms.data, current_user)
            if pdf_file:
                conf.promoter_terms = pdf_file
                db.session.commit()
                flash("New promoter terms uploaded.")
            return redirect(url_for("settings.index"))
        if remove_promoter_terms_form.promoter_remove_terms.name in request.form:
            conf.promoter_terms_id = None
            db.session.commit()
            flash("Promoter terms removed. There are no terms available to view.", "warning")
            return redirect(url_for("settings.index"))
    return render_template("settings/index.html", settings_form=settings_form, conf=conf,
                           terms_form=terms_form, remove_terms_form=remove_terms_form,
                           promoter_terms_form=promoter_terms_form,
                           remove_promoter_terms_form=remove_promoter_terms_form)


@bp.route("/terms", methods=[GET])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def terms():
    file = config().terms
    if file:
        return send_from_directory(file.directory, filename=file.filename, as_attachment=True, cache_timeout=0,
                                   attachment_filename="terms.pdf")
    return abort(404)


@bp.route("/promoter_terms", methods=[GET])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def promoter_terms():
    file = config().promoter_terms
    if file:
        return send_from_directory(file.directory, filename=file.filename, as_attachment=True, cache_timeout=0,
                                   attachment_filename="terms.pdf")
    return abort(404)
