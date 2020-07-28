from flask_wtf import FlaskForm
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from models import Purchase, Refund, Invoice


class PreviewPurchaseForm(FlaskForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.purchase.query = Purchase.query

    purchase = QuerySelectField("Purchase", validators=[DataRequired()])
    view_receipt = SubmitField("View receipt")
    view_tickets = SubmitField("View tickets")


class PreviewRefundForm(FlaskForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.refund.query = Refund.query

    refund = QuerySelectField("Refund", validators=[DataRequired()])
    view_receipt = SubmitField("View receipt")


class PreviewInvoiceForm(FlaskForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.invoice.query = Invoice.query

    invoice = QuerySelectField("Invoice", validators=[DataRequired()])
    view_invoice = SubmitField("View invoice")
