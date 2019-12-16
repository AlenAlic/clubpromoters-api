from flask import render_template
from backend.email import send_email


def send_purchased_tickets(purchase):
    send_email(f"Tickets for {purchase.party}",
               recipients=[purchase.email], bcc=[],
               text_body=render_template('email/purchased_tickets.txt', purchase=purchase),
               html_body=render_template('email/purchased_tickets.html', purchase=purchase))
