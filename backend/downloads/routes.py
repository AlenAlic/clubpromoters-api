from flask import render_template, current_app, request, send_from_directory, redirect, url_for, flash
from flask_login import login_required
from backend.downloads import bp
from models import requires_access_level
from models.user.constants import ACCESS_ADMIN, ACCESS_ORGANIZER
from constants import *
from .functions import get_files


@bp.route("/", methods=[GET, POST])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def index():
    receipts = get_files(current_app.receipts_folder)
    tickets = get_files(current_app.tickets_folder)
    invoices = get_files(current_app.invoices_folder)
    if request.method == POST:
        folder, name = None, None
        receipt = request.form.get("receipt", None)
        if receipt:
            folder = current_app.receipts_folder
            name = receipt
        ticket = request.form.get("ticket", None)
        if ticket:
            folder = current_app.tickets_folder
            name = ticket
        invoice = request.form.get("invoice", None)
        if invoice:
            folder = current_app.invoices_folder
            name = invoice
        if folder and name:
            return send_from_directory(directory=folder, filename=name,
                                       mimetype="application/pdf", as_attachment=True, cache_timeout=0)
        flash("Could not find file")
        return redirect(url_for("downloads.index"))
    return render_template("downloads/index.html", receipts=receipts, invoices=invoices, tickets=tickets)
