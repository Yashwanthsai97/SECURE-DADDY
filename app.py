import io
import requests
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import whois
from datetime import datetime, timezone
from PyPDF2 import PdfReader, PdfWriter
from metadata_utils import analyze_uploaded_file


app = Flask(__name__)
CORS(app)

def normalize_date(date_value):
    if isinstance(date_value, list):
        date_value = date_value[0]

    if isinstance(date_value, datetime):
        if date_value.tzinfo is None:
            return date_value.replace(tzinfo=timezone.utc)
        return date_value

    return None
# ip intelligence tools
@app.route("/ip")
def ip_page():
    return render_template("ip_intelligence.html")


@app.route("/api/ip")
def ip_lookup():
    ip = request.args.get("ip")

    if not ip:
        return jsonify({"error": "No IP provided"}), 400

    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()
        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/")
def home():
    return render_template("main_page.html")

@app.route("/osint")
def osint_page():
    return render_template("osint_tools_page.html")

@app.route("/whois")
def whois_page():
    return render_template("whois.html")

@app.route("/pdftool")
def pdf_tool_page():   # ✅ different name
    return render_template("pdf-tool.html")

@app.route("/metadata")
def metadata_page():
    return render_template("metadata_extractor.html")

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
            mimetype="application/pdf"
        )
    except Exception as error:
        return jsonify({"error": f"Unlock failed: {error}"}), 500

@app.route("/api/whois")
def whois_lookup():
    domain = request.args.get("domain")
    if not domain:
        return jsonify({"error": "No domain provided"}), 400
        

    try:
        w = whois.whois(domain)

        creation_date = normalize_date(w.creation_date)
        expiration_date = normalize_date(w.expiration_date)
        updated_date = normalize_date(w.updated_date)

        now = datetime.now(timezone.utc)
        domain_age_days = None
        if creation_date:
            domain_age_days = (now - creation_date).days

        return jsonify({
            "domain_name": w.domain_name,
            "registrar": w.registrar,
            "whois_server": w.whois_server,
            "status": w.status,
            "creation_date": str(creation_date),
            "expiration_date": str(expiration_date),
            "updated_date": str(updated_date),
            "domain_age_days": domain_age_days,
            "name_servers": w.name_servers,
            "name": w.name,
            "org": w.org,
            "emails": w.emails,
            "phone": w.phone,
            "address": w.address,
            "city": w.city,
            "state": w.state,
            "zipcode": w.zipcode,
            "country": w.country
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
