from flask import render_template

from services.user_store import current_user


def register_home_routes(app):
    @app.route("/")
    def home():
        return render_template("main_page.html", current_user=current_user())
