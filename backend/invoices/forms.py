from flask_wtf import FlaskForm
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from models import Purchase


class TestInvoiceForm(FlaskForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.purchase.query = Purchase.query

    purchase = QuerySelectField("Purchase", validators=[DataRequired()])
    submit = SubmitField("Generate Invoice")
