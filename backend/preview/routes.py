from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from backend.preview import bp
from models import requires_access_level
from models.user.constants import ACCESS_ADMIN
from constants import *
from .forms import PreviewPurchaseForm, PreviewRefundForm, PreviewInvoiceForm
from ext import db
from models import Purchase, Refund, Invoice
from models.configuration import config


@bp.route("/", methods=[GET, POST])
@login_required
@requires_access_level(ACCESS_ADMIN)
def index():
    purchase_form = PreviewPurchaseForm()
    refund_form = PreviewRefundForm()
    invoice_form = PreviewInvoiceForm()
    if request.method == POST:
        if purchase_form.validate_on_submit():
            p = purchase_form.purchase.data
            if not p.receipts_file_exists:
                p.generate_receipt()
                db.session.commit()
            if not p.tickets_file_exists:
                p.generate_tickets()
                db.session.commit()
            if purchase_form.view_receipt.name in request.form:
                return redirect(url_for("preview.purchase_nr", purchase_id=p.purchase_id))
            if purchase_form.view_tickets.name in request.form:
                return redirect(url_for("preview.ticket_nr", purchase_id=p.purchase_id))
        if refund_form.validate_on_submit():
            r = refund_form.refund.data
            if not r.receipts_file_exists:
                r.generate_receipt()
                db.session.commit()
            return redirect(url_for("preview.refund_nr", refund_id=r.refund_id))
        if invoice_form.validate_on_submit():
            i = invoice_form.invoice.data
            return redirect(url_for("preview.invoice_nr", invoice_id=i.invoice_id))
        return redirect(url_for("preview.index"))
    return render_template("preview/index.html", purchase_form=purchase_form, refund_form=refund_form,
                           invoice_form=invoice_form)


@bp.route("/<int:purchase_id>/receipt", methods=[GET])
@login_required
@requires_access_level(ACCESS_ADMIN)
def purchase_nr(purchase_id):
    purchase = Purchase.query.filter(Purchase.purchase_id == purchase_id).first()
    if purchase:
        purchase.generate_receipt()
        db.session.commit()
        return render_template("receipts/receipt_template.html", purchase=purchase, conf=config(), title="Receipt")
    flash("Purchase not found")
    return redirect(url_for("preview.index"))


@bp.route("/<int:purchase_id>/ticket", methods=[GET])
@login_required
@requires_access_level(ACCESS_ADMIN)
def ticket_nr(purchase_id):
    purchase = Purchase.query.filter(Purchase.purchase_id == purchase_id).first()
    if purchase:
        purchase.generate_tickets()
        db.session.commit()
        return render_template("tickets/ticket_template.html", purchase=purchase, conf=config())
    flash("Purchase not found")
    return redirect(url_for("preview.index"))


@bp.route("/<int:refund_id>/refund", methods=[GET])
@login_required
@requires_access_level(ACCESS_ADMIN)
def refund_nr(refund_id):
    refund = Refund.query.filter(Refund.refund_id == refund_id).first()
    if refund:
        refund.generate_receipt()
        db.session.commit()
        return render_template("receipts/receipt_template.html", purchase=refund.purchase, conf=config(), refund=refund)
    flash("Refund not found")
    return redirect(url_for("preview.index"))


@bp.route("/<int:invoice_id>/invoice", methods=[GET])
@login_required
@requires_access_level(ACCESS_ADMIN)
def invoice_nr(invoice_id):
    invoice = Invoice.query.filter(Invoice.invoice_id == invoice_id).first()
    if invoice:
        return render_template("invoices/invoice_template.html", invoice=invoice)
    flash("Invoice not found")
    return redirect(url_for("preview.index"))
