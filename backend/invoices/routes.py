from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from backend.invoices import bp
from models import requires_access_level
from models.user.constants import ACCESS_ADMIN, ACCESS_ORGANIZER
from constants import *
from .forms import InvoiceSettingsForm, BookkeepingEmailForm
from ext import db
from models import Invoice


@bp.route("/", methods=[GET, POST])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def index():
    settings_form = InvoiceSettingsForm()
    bookkeeping_form = BookkeepingEmailForm()
    if request.method == POST:
        if bookkeeping_form.save_email.name in request.form and bookkeeping_form.validate_on_submit():
            bookkeeping_form.save()
            flash("Bookkeeping program email address saved.")
            db.session.commit()
            return redirect(url_for("invoices.index"))
        if settings_form.save_changes.name in request.form and settings_form.validate_on_submit():
            settings_form.save()
            flash("Invoice settings saved.")
            db.session.commit()
            return redirect(url_for("invoices.index"))
    return render_template("invoices/index.html", bookkeeping_form=bookkeeping_form, settings_form=settings_form)


@bp.route("/<int:invoice_id>", methods=[GET])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def invoice_nr(invoice_id):
    invoice = Invoice.query.filter(Invoice.invoice_id == invoice_id).first()
    if invoice:
        return render_template("invoices/invoice_template.html", invoice=invoice)
    flash("Invoice not found")
    return redirect(url_for("invoices.index"))
