from flask import request
from flask_wtf import FlaskForm
from wtforms import SubmitField
from wtforms.fields.html5 import EmailField
from models.configuration import config
from constants import GET


class TestEmailForm(FlaskForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if request.method == GET:
            conf = config()
            self.test_email.data = conf.test_email

    test_email = EmailField("E-mail")
    save_email = SubmitField("Save e-mail")

    def save(self):
        conf = config()
        conf.test_email = self.test_email.data
