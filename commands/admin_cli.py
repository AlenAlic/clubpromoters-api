from flask import current_app
import click
from flask.cli import with_appcontext
from ext import db
from models import User, Configuration
from models.user.constants import ACCESS_ADMIN


@click.group()
def admin():
    """Manages admins (mainly used for adding the first admin)"""
    pass


@admin.command("add")
@click.option("-email", help="E-mail address")
@click.option("-p", help="Password")
@click.option("-fn", default=None, help="First name")
@click.option("-ln", default=None, help="Last name")
@with_appcontext
def create_admin(email, p, fn, ln):
    usr = User(email, p)
    usr.first_name = fn
    usr.last_name = ln
    usr.access = ACCESS_ADMIN
    usr.is_active = True
    db.session.add(usr)
    db.session.commit()
    print(f"User added: {usr}")


@admin.command("password")
@click.option("-email", help="User email")
@click.option("-p", help="New password")
@with_appcontext
def set_password(email, p):
    usr = User.query.filter(User.email.ilike(email)).first()
    if usr is not None:
        usr.set_password(p)
        db.session.commit()
        print(f"Password set for user: {usr}")
    else:
        print(f"Could not find user with email: '{email}'")


@admin.command("config")
@with_appcontext
def create_config():
    if len(Configuration.query.all()) == 0:
        conf = Configuration()
        if current_app.config.get("MOLLIE_API_KEY") is not None:
            current_app.mollie_api_key = current_app.config.get("MOLLIE_API_KEY")
            print("Mollie API key added")
        db.session.add(conf)
        db.session.commit()
        print("Configuration added")
