from flask import redirect, url_for
from flask_login import current_user
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView


class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for("main.index"))
        else:
            # TODO Add items to admin home page
            return self.render(self._template)


class BaseView(ModelView):
    column_display_pk = True

    form_excluded_columns = ["created_at", "updated_at"]
    column_exclude_list = ["created_at", "updated_at"]

    column_hide_backrefs = False

    page_size = 200

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("main.index"))


class UserView(BaseView):
    form_excluded_columns = ["created_at", "updated_at", "password_hash", ]
