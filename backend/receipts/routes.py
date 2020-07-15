from flask import render_template, request, current_app, send_from_directory, flash, redirect, url_for
from flask_login import login_required
from backend.receipts import bp
from models import requires_access_level
from models.user.constants import ACCESS_ADMIN, ACCESS_ORGANIZER
from constants import *
from .forms import TestReceiptForm, ReceiptSettingsForm
from ext import db
from models import Purchase, Refund
from models.configuration import config


@bp.route("/", methods=[GET, POST])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def index():
    receipt_form = TestReceiptForm()
    settings_form = ReceiptSettingsForm()
    if request.method == POST:
        if settings_form.save_changes.name in request.form and settings_form.validate_on_submit():
            settings_form.save()
            flash("Receipt settings saved.")
            db.session.commit()
            return redirect(url_for("receipts.index"))
        p = receipt_form.purchase.data
        if p and receipt_form.validate_on_submit():
            if not p.receipts_file_exists:
                p.generate_receipt()
                db.session.commit()
            if not p.tickets_file_exists:
                p.generate_tickets()
                db.session.commit()
            if receipt_form.view_receipt.name in request.form:
                return send_from_directory(directory=current_app.receipts_folder, filename=p.receipt_file_name,
                                           mimetype="application/pdf", as_attachment=True, cache_timeout=0)
            if receipt_form.view_tickets.name in request.form:
                return send_from_directory(directory=current_app.tickets_folder, filename=p.tickets_file_name,
                                           mimetype="application/pdf", as_attachment=True, cache_timeout=0)
        return redirect(url_for("receipts.index"))
    return render_template("receipts/index.html", receipt_form=receipt_form, settings_form=settings_form)


@bp.route("/<int:purchase_id>", methods=[GET])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def purchase_nr(purchase_id):
    purchase = Purchase.query.filter(Purchase.purchase_id == purchase_id).first()
    if purchase:
        return render_template("receipts/receipt_template.html", purchase=purchase, conf=config())
    flash("Purchase not found")
    return redirect(url_for("receipt.index"))


@bp.route("/<int:refund_id>/refund", methods=[GET])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def refund_nr(refund_id):
    refund = Refund.query.filter(Refund.refund_id == refund_id).first()
    if refund:
        return render_template("receipts/receipt_template.html", purchase=refund.purchase, conf=config(), refund=refund)
    flash("Refund not found")
    return redirect(url_for("receipt.index"))
