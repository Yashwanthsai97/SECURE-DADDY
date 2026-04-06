from datetime import datetime, timezone

import whois
from flask import jsonify, render_template, request


def normalize_date(date_value):
    if isinstance(date_value, list):
        date_value = date_value[0]

    if isinstance(date_value, datetime):
        if date_value.tzinfo is None:
            return date_value.replace(tzinfo=timezone.utc)
        return date_value

    return None


def register_whois_routes(app):
    @app.route("/whois")
    def whois_page():
        return render_template("whois.html")

    @app.route("/api/whois")
    def whois_lookup():
        domain = request.args.get("domain")
        if not domain:
            return jsonify({"error": "No domain provided"}), 400

        try:
            result = whois.whois(domain)

            creation_date = normalize_date(result.creation_date)
            expiration_date = normalize_date(result.expiration_date)
            updated_date = normalize_date(result.updated_date)

            now = datetime.now(timezone.utc)
            domain_age_days = None
            if creation_date:
                domain_age_days = (now - creation_date).days

            return jsonify(
                {
                    "domain_name": result.domain_name,
                    "registrar": result.registrar,
                    "whois_server": result.whois_server,
                    "status": result.status,
                    "creation_date": str(creation_date),
                    "expiration_date": str(expiration_date),
                    "updated_date": str(updated_date),
                    "domain_age_days": domain_age_days,
                    "name_servers": result.name_servers,
                    "name": result.name,
                    "org": result.org,
                    "emails": result.emails,
                    "phone": result.phone,
                    "address": result.address,
                    "city": result.city,
                    "state": result.state,
                    "zipcode": result.zipcode,
                    "country": result.country,
                }
            )
        except Exception as error:
            return jsonify({"error": str(error)}), 500
