from flask import render_template

from services.user_store import current_user, profile_completion_score


def register_signin_routes(app):
    @app.route("/signin")
    def signin_page():
        user = current_user()
        return render_template(
            "signin.html",
            current_user=user,
            completion_score=profile_completion_score(user),
        )
