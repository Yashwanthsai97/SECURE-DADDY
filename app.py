import io
import json
from datetime import datetime, timezone
from datetime import timedelta
from pathlib import Path

import requests
import whois
from flask import Flask, request, jsonify, render_template, send_file, session
from flask_cors import CORS
from PyPDF2 import PdfReader, PdfWriter
from werkzeug.security import check_password_hash, generate_password_hash

from metadata_utils import analyze_uploaded_file


# ============================================================================
# APP SETUP AND CONFIGURATION
# ============================================================================

app = Flask(__name__)
CORS(app)
app.secret_key = "secure-daddy-dev-secret"
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

BASE_DIR = Path(__file__).resolve().parent
USER_DB_PATH = BASE_DIR / "users.json"
IST = timezone(timedelta(hours=5, minutes=30))


# ============================================================================
# LOCAL USER STORAGE HELPERS
# ============================================================================

def load_users():
    if not USER_DB_PATH.exists():
        return {}

    try:
        return json.loads(USER_DB_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_users(users):
    USER_DB_PATH.write_text(json.dumps(users, indent=2), encoding="utf-8")


# ============================================================================
# SESSION AND DATA NORMALIZATION HELPERS
# ============================================================================

DEFAULT_PROFILE_VALUES = {
    "role": "Security Analyst",
    "company": "Independent Research",
    "location": "Hyderabad, India",
    "focus_area": "OSINT & Metadata Analysis",
    "bio": "Tracking digital footprints, validating evidence, and building sharper security workflows.",
    "website": "",
    "headline": "Security analyst building practical cyber workflows.",
    "profile_picture": "",
    "facebook_url": "",
    "instagram_url": "",
    "linkedin_url": "",
    "tiktok_url": "",
    "x_url": "",
    "youtube_url": "",
    "show_profile_to_logged_in_users": True,
    "show_activity_on_profile": True,
    "created_at": None,
    "last_login_at": None,
}


def hydrate_user(user):
    if not user:
        return None

    enriched_user = {**DEFAULT_PROFILE_VALUES, **user}
    enriched_user["name"] = (enriched_user.get("name") or "SecureDaddy User").strip()
    enriched_user["email"] = (enriched_user.get("email") or "").strip().lower()
    enriched_user["company"] = (enriched_user.get("company") or DEFAULT_PROFILE_VALUES["company"]).strip()
    enriched_user["location"] = (enriched_user.get("location") or DEFAULT_PROFILE_VALUES["location"]).strip()
    enriched_user["role"] = (enriched_user.get("role") or DEFAULT_PROFILE_VALUES["role"]).strip()
    enriched_user["focus_area"] = (enriched_user.get("focus_area") or DEFAULT_PROFILE_VALUES["focus_area"]).strip()
    enriched_user["bio"] = (enriched_user.get("bio") or DEFAULT_PROFILE_VALUES["bio"]).strip()
    enriched_user["headline"] = (enriched_user.get("headline") or DEFAULT_PROFILE_VALUES["headline"]).strip()
    enriched_user["website"] = (enriched_user.get("website") or "").strip()
    enriched_user["profile_picture"] = (enriched_user.get("profile_picture") or "").strip()
    enriched_user["facebook_url"] = (enriched_user.get("facebook_url") or "").strip()
    enriched_user["instagram_url"] = (enriched_user.get("instagram_url") or "").strip()
    enriched_user["linkedin_url"] = (enriched_user.get("linkedin_url") or "").strip()
    enriched_user["tiktok_url"] = (enriched_user.get("tiktok_url") or "").strip()
    enriched_user["x_url"] = (enriched_user.get("x_url") or "").strip()
    enriched_user["youtube_url"] = (enriched_user.get("youtube_url") or "").strip()
    enriched_user["show_profile_to_logged_in_users"] = bool(enriched_user.get("show_profile_to_logged_in_users", True))
    enriched_user["show_activity_on_profile"] = bool(enriched_user.get("show_activity_on_profile", True))
    enriched_user["initials"] = "".join(
        part[0].upper() for part in enriched_user["name"].split() if part
    )[:2] or "SD"
    enriched_user["created_at_display"] = format_profile_timestamp(
        enriched_user.get("created_at") or enriched_user.get("last_login_at")
    )
    enriched_user["last_login_at_display"] = format_profile_timestamp(enriched_user.get("last_login_at"))
    return enriched_user

def current_user():
    user_email = session.get("user_email")
    if not user_email:
        return None

    return hydrate_user(load_users().get(user_email))


def normalize_date(date_value):
    if isinstance(date_value, list):
        date_value = date_value[0]

    if isinstance(date_value, datetime):
        if date_value.tzinfo is None:
            return date_value.replace(tzinfo=timezone.utc)
        return date_value

    return None


def format_profile_timestamp(value):
    if not value:
        return "Not available yet"

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        parsed = parsed.astimezone(IST)
        return parsed.strftime("%d %b %Y, %I:%M %p IST")
    except ValueError:
        return str(value)


def profile_completion_score(user):
    fields = [
        "name",
        "email",
        "role",
        "company",
        "location",
        "focus_area",
        "bio",
        "headline",
        "website",
        "profile_picture",
    ]
    completed = sum(1 for field in fields if (user.get(field) or "").strip())
    return round((completed / len(fields)) * 100)


# ============================================================================
# PAGE ROUTES
# ============================================================================

@app.route("/")
def home():
    return render_template("main_page.html", current_user=current_user())


@app.route("/signin")
def signin_page():
    user = current_user()
    return render_template(
        "signin.html",
        current_user=user,
        completion_score=profile_completion_score(user) if user else 0,
    )


@app.route("/osint")
def osint_page():
    return render_template("osint_tools_page.html")


@app.route("/ip")
def ip_page():
    return render_template("ip_intelligence.html")


@app.route("/whois")
def whois_page():
    return render_template("whois.html")


@app.route("/pdftool")
def pdf_tool_page():
    return render_template("pdf-tool.html")


@app.route("/metadata")
def metadata_page():
    return render_template("metadata_extractor.html")


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route("/api/auth/signup", methods=["POST"])
def signup():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required."}), 400

    users = load_users()
    if email in users:
        return jsonify({"error": "An account already exists for this email."}), 409

    users[email] = {
        "name": name,
        "email": email,
        "password_hash": generate_password_hash(password),
        "role": DEFAULT_PROFILE_VALUES["role"],
        "company": DEFAULT_PROFILE_VALUES["company"],
        "location": DEFAULT_PROFILE_VALUES["location"],
        "focus_area": DEFAULT_PROFILE_VALUES["focus_area"],
        "bio": DEFAULT_PROFILE_VALUES["bio"],
        "website": DEFAULT_PROFILE_VALUES["website"],
        "headline": DEFAULT_PROFILE_VALUES["headline"],
        "profile_picture": DEFAULT_PROFILE_VALUES["profile_picture"],
        "facebook_url": DEFAULT_PROFILE_VALUES["facebook_url"],
        "instagram_url": DEFAULT_PROFILE_VALUES["instagram_url"],
        "linkedin_url": DEFAULT_PROFILE_VALUES["linkedin_url"],
        "tiktok_url": DEFAULT_PROFILE_VALUES["tiktok_url"],
        "x_url": DEFAULT_PROFILE_VALUES["x_url"],
        "youtube_url": DEFAULT_PROFILE_VALUES["youtube_url"],
        "show_profile_to_logged_in_users": DEFAULT_PROFILE_VALUES["show_profile_to_logged_in_users"],
        "show_activity_on_profile": DEFAULT_PROFILE_VALUES["show_activity_on_profile"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login_at": datetime.now(timezone.utc).isoformat(),
    }
    save_users(users)

    session.clear()
    session.permanent = True
    session["user_email"] = email
    return jsonify({"message": "Account created successfully.", "redirect": "/"})


@app.route("/api/auth/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    users = load_users()
    user = users.get(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password."}), 401

    user["last_login_at"] = datetime.now(timezone.utc).isoformat()
    users[email] = user
    save_users(users)

    session.clear()
    session.permanent = True
    session["user_email"] = email
    return jsonify({"message": "Signed in successfully.", "redirect": "/"})


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.pop("user_email", None)
    return jsonify({"message": "Signed out successfully.", "redirect": "/"})


@app.route("/api/profile", methods=["POST"])
def update_profile():
    user_email = session.get("user_email")
    if not user_email:
        return jsonify({"error": "You must be signed in to update your profile."}), 401

    payload = request.get_json(silent=True) or {}
    users = load_users()
    user = users.get(user_email)
    if not user:
        return jsonify({"error": "Account not found."}), 404

    updated_fields = {
        "name": (payload.get("name") or "").strip(),
        "role": (payload.get("role") or "").strip(),
        "company": (payload.get("company") or "").strip(),
        "location": (payload.get("location") or "").strip(),
        "focus_area": (payload.get("focus_area") or "").strip(),
        "website": (payload.get("website") or "").strip(),
        "headline": (payload.get("headline") or "").strip(),
        "profile_picture": (payload.get("profile_picture") or "").strip(),
        "facebook_url": (payload.get("facebook_url") or "").strip(),
        "instagram_url": (payload.get("instagram_url") or "").strip(),
        "linkedin_url": (payload.get("linkedin_url") or "").strip(),
        "tiktok_url": (payload.get("tiktok_url") or "").strip(),
        "x_url": (payload.get("x_url") or "").strip(),
        "youtube_url": (payload.get("youtube_url") or "").strip(),
        "bio": (payload.get("bio") or "").strip(),
    }

    if not updated_fields["name"]:
        return jsonify({"error": "Name is required."}), 400

    for key, value in updated_fields.items():
        user[key] = value if value else DEFAULT_PROFILE_VALUES.get(key, "")

    user["show_profile_to_logged_in_users"] = bool(payload.get("show_profile_to_logged_in_users", True))
    user["show_activity_on_profile"] = bool(payload.get("show_activity_on_profile", True))

    users[user_email] = user
    save_users(users)

    hydrated = hydrate_user(user)
    return jsonify({
        "message": "Profile updated successfully.",
        "user": hydrated,
        "completion_score": profile_completion_score(hydrated),
    })


# ============================================================================
# IP INTELLIGENCE ROUTES
# ============================================================================

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


# ============================================================================
# METADATA TOOL ROUTES
# ============================================================================

@app.route("/api/metadata/analyze", methods=["POST"])
def metadata_analyze():
    uploaded_file = request.files.get("file")

    if not uploaded_file:
        return jsonify({"error": "No file was uploaded."}), 400

    try:
        return jsonify(analyze_uploaded_file(uploaded_file))
    except Exception as error:
        return jsonify({"error": f"Metadata analysis failed: {error}"}), 500


# ============================================================================
# PDF TOOL ROUTES
# ============================================================================

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


# ============================================================================
# WHOIS LOOKUP ROUTES
# ============================================================================

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


# ============================================================================
# DEVELOPMENT ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    app.run(debug=True)
