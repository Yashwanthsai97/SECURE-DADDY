from datetime import timedelta

from flask import Flask
from flask_cors import CORS

from routes.auth_routes import register_auth_routes
from routes.home_routes import register_home_routes
from routes.ip_routes import register_ip_routes
from routes.metadata_routes import register_metadata_routes
from routes.osint_routes import register_osint_routes
from routes.pdf_routes import register_pdf_routes
from routes.profile_routes import register_profile_routes
from routes.signin_routes import register_signin_routes
from routes.whois_routes import register_whois_routes


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.secret_key = "secure-daddy-dev-secret"
    app.config["SESSION_PERMANENT"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

    register_home_routes(app)
    register_signin_routes(app)
    register_osint_routes(app)
    register_ip_routes(app)
    register_whois_routes(app)
    register_pdf_routes(app)
    register_metadata_routes(app)
    register_auth_routes(app)
    register_profile_routes(app)

    return app
