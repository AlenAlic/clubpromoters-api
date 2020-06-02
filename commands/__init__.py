from .admin_cli import admin


def init_app(app):
    app.cli.add_command(admin)
