from flask import render_template, session

from models.user_model import get_hydrated_user_by_email
from utils.profile import profile_completion_score


def current_user():
    user_email = session.get("user_email")
    if not user_email:
        return None

    return get_hydrated_user_by_email(user_email)


def home():
    return render_template("main_page.html", current_user=current_user())


def signin_page():
    user = current_user()
    return render_template(
        "signin.html",
        current_user=user,
        completion_score=profile_completion_score(user) if user else 0,
    )


def osint_page():
    return render_template("osint_tools_page.html")


def ip_page():
    return render_template("ip_intelligence.html")


def whois_page():
    return render_template("whois.html")


def pdf_tool_page():
    return render_template("pdf-tool.html")


def metadata_page():
    return render_template("metadata_extractor.html")


def register_page_routes(app):
    app.add_url_rule("/", endpoint="home", view_func=home)
    app.add_url_rule("/signin", endpoint="signin_page", view_func=signin_page)
    app.add_url_rule("/osint", endpoint="osint_page", view_func=osint_page)
    app.add_url_rule("/ip", endpoint="ip_page", view_func=ip_page)
    app.add_url_rule("/whois", endpoint="whois_page", view_func=whois_page)
    app.add_url_rule("/pdftool", endpoint="pdf_tool_page", view_func=pdf_tool_page)
    app.add_url_rule("/metadata", endpoint="metadata_page", view_func=metadata_page)
