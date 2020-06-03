from flask import render_template, request, current_app, send_from_directory
from flask_login import login_required
from backend.invoices import bp
from models import requires_access_level
from models.user.constants import ACCESS_ADMIN, ACCESS_ORGANIZER
from constants import *
from .forms import TestInvoiceForm
from weasyprint import HTML
import os


@bp.route("/", methods=[GET, POST])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def index():
    form = TestInvoiceForm()
    if request.method == POST:
        p = form.purchase.data
        directory = os.path.join(current_app.static_folder, UPLOAD_FOLDER)
        file_name = f"invoice.{p.purchase_id}.pdf"
        path = os.path.join(directory, file_name)
        if form.validate_on_submit():
            HTML(string=render_template("invoices/invoice_template.html", purchase=p),
                 base_url=request.base_url).write_pdf(path)
            # return render_template("invoices/invoice_template.html", purchase=p)
            return send_from_directory(directory=directory, filename=file_name, mimetype="application/pdf")
    return render_template("invoices/index.html", form=form)
