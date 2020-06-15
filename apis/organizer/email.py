from flask import render_template
from mailing import send_email


def send_invoice(invoice):
    from models.configuration import config
    conf = config()
    send_email(
        f"{'Factuur' if invoice.dutch else 'Invoice'} {invoice.delivery_date}",
        recipients=[invoice.user.email],
        bcc=[conf.bookkeeping_program_email],
        text_body=render_template("email/invoices/send_invoice.txt", invoice=invoice),
        html_body=render_template("email/invoices/send_invoice.html", invoice=invoice),
        attachments={invoice.filename: invoice.path}
    )
