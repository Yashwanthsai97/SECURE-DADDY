import re


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9._@-]{3,255}$")


def validate_email(email):
    return bool(EMAIL_PATTERN.match((email or "").strip()))


def normalize_login_identifier(value):
    return (value or "").strip().lower()


def validate_signup_payload(payload):
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    username = normalize_login_identifier(payload.get("username") or email)
    password = payload.get("password") or ""

    if not name or not email or not password:
        return ["Name, email, and password are required."]

    if not validate_email(email):
        return ["Please enter a valid email address."]

    if len(password) < 6:
        return ["Password must be at least 6 characters long."]

    if not USERNAME_PATTERN.match(username):
        return ["Username may only contain letters, numbers, dots, underscores, hyphens, and @."]

    return []
