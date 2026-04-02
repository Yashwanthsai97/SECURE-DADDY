from controllers.auth_controller import login, signup


def register_auth_routes(app):
    app.add_url_rule("/api/auth/signup", endpoint="signup", view_func=signup, methods=["POST"])
    app.add_url_rule("/api/auth/login", endpoint="login", view_func=login, methods=["POST"])
