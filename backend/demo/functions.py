from models import Party, PartyFile, Purchase, Code, Ticket, Refund
from datetime import datetime, timedelta
from ext import db
from random import choice, shuffle
from .data import PROMOTER_CODES, BUYERS
from models.configuration import config
from constants import STATUS_PAID, LOCAL_TIMEZONE
import pytz


def preset_start_datetime():
    date = datetime.utcnow()
    start_date = datetime(date.year, date.month, date.day, 22, 30)
    amsterdam_start_date = LOCAL_TIMEZONE.localize(start_date)
    amsterdam_start_date = amsterdam_start_date.astimezone(pytz.utc)
    return amsterdam_start_date


def create_party(club, start_date):
    conf = config()
    party = Party()
    party.is_active = True
    party.club_owner = club
    party.name = f"{start_date.strftime('%A')} party"
    party.location = club.locations[0]
    party.party_start_datetime = start_date + timedelta(hours=choice([-1, 0, 1]))
    party.party_end_datetime = party.party_start_datetime + timedelta(hours=choice([5, 6, 7]))
    party.description = "Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n" \
                        "Nunc pretium, tellus nec molestie tempor, purus dolor dictum leo, " \
                        "at consectetur odio felis non dolor.\n\n" \
                        "Donec posuere odio nec justo aliquam dignissim."
    party.num_available_tickets = choice([80, 100, 120])
    party.ticket_price = choice([1500, 2000, 2500, 3000])
    party.club_owner_commission = 40
    party.promoter_commission = 10
    party.interval = choice([200, 300, 400])
    logos = [f for f in party.club_owner.files if f.logo]
    shuffle(logos)
    party.logo = logos[0]
    images = [f for f in party.club_owner.files if not f.logo]
    shuffle(images)
    images = images[0:choice([3, 4, 5])]
    for idx, file in enumerate(images):
        party_file = PartyFile()
        party_file.order = idx
        party_file.file = file
        party_file.party = party
    db.session.add(party)
    db.session.flush()
    for p in range(choice([5, 6, 7, 8, 9])):
        tickets = choice([2, 3, 4])
        purchase = Purchase()
        purchase.status = STATUS_PAID
        purchase.party = party
        buyer = choice(BUYERS)
        purchase.purchase_datetime = start_date - timedelta(days=2)
        purchase.email = buyer["email"]
        purchase.first_name = buyer["first_name"]
        purchase.last_name = buyer["last_name"]
        purchase.code = Code.query.filter(Code.code == choice(PROMOTER_CODES)).first()
        purchase.promoter = purchase.code.user
        purchase.set_commissions()
        purchase.ticket_price = party.ticket_price
        purchase.administration_costs = conf.administration_costs
        purchase.price = party.ticket_price * tickets
        purchase.vat_percentage = conf.vat
        purchase.mollie_payment_id = f"purchase_{datetime.utcnow().timestamp()}"
        purchase.minimum_promoter_commission = purchase.code.user.minimum_promoter_commission
        db.session.add(purchase)
        db.session.flush()
        purchase.set_hash()
        for i in range(tickets):
            t = Ticket()
            t.number = i + 1
            purchase.tickets.append(t)
        tickets_refunded = choice([0, 0, 0, 1, 2])
        for i in range(tickets_refunded):
            ref = Refund()
            ref.price = party.ticket_price * tickets_refunded
            ref.purchase = purchase
            ref.mollie_refund_id = f"refund_{datetime.utcnow().timestamp()}"
            db.session.add(ref)
            purchase.tickets[i].refund = ref
