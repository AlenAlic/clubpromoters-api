from flask import render_template
from mailing import send_email


def send_receipt(purchase):
    send_email(f"Receipt for {purchase.party}",
               recipients=[purchase.email], bcc=[],
               text_body=render_template("email/purchase/receipt.txt", purchase=purchase),
               html_body=render_template("email/purchase/receipt.html", purchase=purchase),
               attachments={"receipt.pdf": purchase.receipt_path}
               )


def send_purchased_tickets(purchase):
    send_email(f"Tickets for {purchase.party}",
               recipients=[purchase.email], bcc=[],
               text_body=render_template("email/purchase/purchased_tickets.txt", purchase=purchase),
               html_body=render_template("email/purchase/purchased_tickets.html", purchase=purchase),
               attachments={"tickets.pdf": purchase.tickets_path}
               )
