from controllers.profile_controller import save_profile


def register_profile_routes(app):
    app.add_url_rule("/api/profile", endpoint="update_profile", view_func=save_profile, methods=["POST"])
