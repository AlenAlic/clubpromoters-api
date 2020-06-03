from flask_admin import Admin
from .views import MyAdminIndexView, BaseView, UserView
from models import User, Location, Party, Purchase, Ticket, Refund, Code, File, PartyFile


admin = Admin(name="clubpromoters.net", template_mode="bootstrap3", index_view=MyAdminIndexView())


def init_app(app, db):
    admin.init_app(app)
    admin.add_view(UserView(User, db.session))
    admin.add_view(BaseView(Location, db.session))
    admin.add_view(BaseView(Party, db.session))
    admin.add_view(BaseView(Purchase, db.session))
    admin.add_view(BaseView(Ticket, db.session))
    admin.add_view(BaseView(Refund, db.session))
    admin.add_view(BaseView(Code, db.session))
    admin.add_view(BaseView(File, db.session))
    admin.add_view(BaseView(PartyFile, db.session))
