from models import User, Purchase, Ticket, Party, Refund
from datetime import datetime, timedelta


def generate_dummy_purchase():
    start_time = datetime.utcnow().replace(hour=22, minute=30)
    usr = User("club@test.com")
    usr.club = "Club"
    party = Party()
    party.party_id = 42
    party.name = "Amazing party"
    party.party_start_datetime = start_time
    party.party_end_datetime = start_time + timedelta(hours=5)
    party.club_owner = usr
    tickets = 3
    purchase = Purchase()
    purchase.party = party
    purchase.party_id = party.party_id
    purchase.purchase_id = 10
    purchase.ticket_price = 2500
    purchase.price = purchase.ticket_price * tickets
    purchase.first_name = "Charlie"
    purchase.last_name = "Brown"
    purchase.email = "c.brown@example.com"
    purchase.mollie_payment_id = "tr_mollieID123"
    purchase.purchase_datetime = datetime.utcnow()
    purchase.hash = purchase.set_hash()
    for i in range(tickets):
        ticket = Ticket()
        ticket.number = i + 1
        purchase.tickets.append(ticket)
    refund = Refund()
    refund.price = 2500
    refund.refund_datetime = datetime.utcnow().replace(hour=23, minute=35)
    refund.purchase = purchase
    refund.refund_number = 1
    return purchase

