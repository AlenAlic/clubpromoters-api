from flask import render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import current_user, login_user, logout_user, login_required
from backend.main import bp
from backend.main.forms import LoginForm
from constants import *
from models import User
import os


@bp.route("/", methods=[GET, POST])
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if request.method == POST:
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user is None or not user.check_password(form.password.data):
                flash("Invalid email or password", "alert-danger")
                return redirect(url_for("main.index"))
            if user.is_active and (user.is_admin or user.is_organizer):
                login_user(user)
                return redirect(url_for("main.dashboard"))
            else:
                flash("Account inactive", "alert-warning")
                return redirect(url_for("main.index"))
    return render_template("main/index.html", login_form=form)


@bp.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, "static"), "favicon.ico")


@bp.route("/dashboard", methods=[GET, POST])
@login_required
def dashboard():
    return render_template("main/dashboard.html")


@bp.route("/logout", methods=[GET])
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))
