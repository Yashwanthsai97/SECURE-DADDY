import io
import sys
from datetime import datetime, timedelta, timezone

import requests
import whois
from flask import Flask, jsonify, request, send_file, session
from flask_cors import CORS
from mysql.connector import Error as MySQLError
from PyPDF2 import PdfReader, PdfWriter

from config.db import init_db
from routes.auth_routes import register_auth_routes
from routes.page_routes import register_page_routes
from routes.profile_routes import register_profile_routes
from utils.profile import normalize_date


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.secret_key = "secure-daddy-dev-secret"
    app.config["SESSION_PERMANENT"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

    init_db()

    register_page_routes(app)
    register_auth_routes(app)
    register_profile_routes(app)
    register_tool_routes(app)
    return app


def register_tool_routes(app):
    from metadata_utils import analyze_uploaded_file

    @app.route("/api/auth/logout", methods=["POST"])
    def logout():
        session.pop("user_email", None)
        return jsonify({"message": "Signed out successfully.", "redirect": "/"})

    @app.route("/api/ip")
    def ip_lookup():
        ip = request.args.get("ip")

        if not ip:
            return jsonify({"error": "No IP provided"}), 400

        try:
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=10)
            return jsonify(response.json())
        except Exception as error:
            return jsonify({"error": str(error)}), 500

    @app.route("/api/metadata/analyze", methods=["POST"])
    def metadata_analyze():
        uploaded_file = request.files.get("file")

        if not uploaded_file:
            return jsonify({"error": "No file was uploaded."}), 400

        try:
            return jsonify(analyze_uploaded_file(uploaded_file))
        except Exception as error:
            return jsonify({"error": f"Metadata analysis failed: {error}"}), 500

    @app.route("/api/pdf/unlock", methods=["POST"])
    def pdf_unlock():
        uploaded_file = request.files.get("file")
        password = (request.form.get("password") or "").strip()

        if not uploaded_file:
            return jsonify({"error": "No PDF file was uploaded."}), 400

        if not password:
            return jsonify({"error": "No password was provided."}), 400

        if not uploaded_file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are supported."}), 400

        try:
            reader = PdfReader(uploaded_file.stream)

            if not reader.is_encrypted:
                return jsonify({"error": "This PDF is not encrypted."}), 400

            decrypt_result = reader.decrypt(password)
            if not decrypt_result:
                return jsonify({"error": "The password was not accepted for this PDF."}), 400

            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)

            if reader.metadata:
                safe_metadata = {}
                for key, value in reader.metadata.items():
                    if value is None:
                        continue
                    safe_metadata[str(key)] = str(value)

                if safe_metadata:
                    writer.add_metadata(safe_metadata)

            output_stream = io.BytesIO()
            writer.write(output_stream)
            output_stream.seek(0)

            original_name = uploaded_file.filename.rsplit(".", 1)[0]
            download_name = f"{original_name}-unlocked.pdf"

            return send_file(
                output_stream,
                as_attachment=True,
                download_name=download_name,
                mimetype="application/pdf",
            )
        except Exception as error:
            return jsonify({"error": f"Unlock failed: {error}"}), 500

    @app.route("/api/whois")
    def whois_lookup():
        domain = request.args.get("domain")
        if not domain:
            return jsonify({"error": "No domain provided"}), 400

        try:
            whois_data = whois.whois(domain)

            creation_date = normalize_date(whois_data.creation_date)
            expiration_date = normalize_date(whois_data.expiration_date)
            updated_date = normalize_date(whois_data.updated_date)

            now = datetime.now(timezone.utc)
            domain_age_days = None
            if creation_date:
                domain_age_days = (now - creation_date).days

            return jsonify(
                {
                    "domain_name": whois_data.domain_name,
                    "registrar": whois_data.registrar,
                    "whois_server": whois_data.whois_server,
                    "status": whois_data.status,
                    "creation_date": str(creation_date),
                    "expiration_date": str(expiration_date),
                    "updated_date": str(updated_date),
                    "domain_age_days": domain_age_days,
                    "name_servers": whois_data.name_servers,
                    "name": whois_data.name,
                    "org": whois_data.org,
                    "emails": whois_data.emails,
                    "phone": whois_data.phone,
                    "address": whois_data.address,
                    "city": whois_data.city,
                    "state": whois_data.state,
                    "zipcode": whois_data.zipcode,
                    "country": whois_data.country,
                }
            )
        except Exception as error:
            return jsonify({"error": str(error)}), 500

if __name__ == "__main__":
    try:
        app = create_app()
        app.run(debug=True)
    except MySQLError as error:
        print("\n[SecureDaddy] MySQL startup error")
        print("The app could not connect to MySQL with the current settings.")
        print("Check D:\\SECURE-DADDY\\.env and confirm MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, and MYSQL_DATABASE are correct.")
        print(f"MySQL said: {error}")
        sys.exit(1)
