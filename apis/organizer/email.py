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


def send_refund_receipt(refund):
    send_email(f"Receipt for {refund.purchase.party}",
               recipients=[refund.purchase.email], bcc=[],
               text_body=render_template("email/purchase/refund_receipt.txt", refund=refund),
               html_body=render_template("email/purchase/refund_receipt.html", refund=refund),
               attachments={"receipt.pdf": refund.receipt_path}
               )
