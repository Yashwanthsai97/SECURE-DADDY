from datetime import datetime, timezone

from config.db import get_db_connection
from utils.profile import DEFAULT_PROFILE_VALUES, hydrate_user


USER_COLUMNS = """
    id,
    username,
    name,
    email,
    password,
    password_algorithm,
    role,
    company,
    location,
    focus_area,
    bio,
    website,
    headline,
    profile_picture,
    facebook_url,
    instagram_url,
    linkedin_url,
    tiktok_url,
    x_url,
    youtube_url,
    show_profile_to_logged_in_users,
    show_activity_on_profile,
    created_at,
    last_login_at
"""


def _serialize_user(row):
    if not row:
        return None

    user = dict(row)
    for field in ("created_at", "last_login_at"):
        value = user.get(field)
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            user[field] = value.isoformat()

    user["show_profile_to_logged_in_users"] = bool(user.get("show_profile_to_logged_in_users"))
    user["show_activity_on_profile"] = bool(user.get("show_activity_on_profile"))
    return user


def get_user_by_email(email):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(f"SELECT {USER_COLUMNS} FROM users WHERE email = %s", (email,))
        return _serialize_user(cursor.fetchone())
    finally:
        cursor.close()
        connection.close()


def get_user_by_username(username):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(f"SELECT {USER_COLUMNS} FROM users WHERE username = %s", (username,))
        return _serialize_user(cursor.fetchone())
    finally:
        cursor.close()
        connection.close()


def get_user_for_login(identifier):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            f"SELECT {USER_COLUMNS} FROM users WHERE username = %s OR email = %s",
            (identifier, identifier),
        )
        return _serialize_user(cursor.fetchone())
    finally:
        cursor.close()
        connection.close()


def create_user(name, email, username, password_hash, password_algorithm="bcrypt", user_data=None):
    defaults = dict(DEFAULT_PROFILE_VALUES)
    for key, value in (user_data or {}).items():
        if value is not None:
            defaults[key] = value
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO users (
                username, name, email, password, password_algorithm, role, company, location,
                focus_area, bio, website, headline, profile_picture, facebook_url, instagram_url,
                linkedin_url, tiktok_url, x_url, youtube_url, show_profile_to_logged_in_users,
                show_activity_on_profile, created_at, last_login_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            """,
            (
                username,
                name,
                email,
                password_hash,
                password_algorithm,
                defaults["role"],
                defaults["company"],
                defaults["location"],
                defaults["focus_area"],
                defaults["bio"],
                defaults["website"],
                defaults["headline"],
                defaults["profile_picture"],
                defaults["facebook_url"],
                defaults["instagram_url"],
                defaults["linkedin_url"],
                defaults["tiktok_url"],
                defaults["x_url"],
                defaults["youtube_url"],
                int(defaults["show_profile_to_logged_in_users"]),
                int(defaults["show_activity_on_profile"]),
                defaults.get("created_at") or datetime.now(timezone.utc),
                defaults.get("last_login_at") or datetime.now(timezone.utc),
            ),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def update_last_login(email):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE users SET last_login_at = UTC_TIMESTAMP() WHERE email = %s",
            (email,),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def update_password(email, password_hash, password_algorithm="bcrypt"):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE users SET password = %s, password_algorithm = %s WHERE email = %s",
            (password_hash, password_algorithm, email),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def update_profile(email, payload):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            UPDATE users
            SET
                name = %s,
                role = %s,
                company = %s,
                location = %s,
                focus_area = %s,
                website = %s,
                headline = %s,
                profile_picture = %s,
                facebook_url = %s,
                instagram_url = %s,
                linkedin_url = %s,
                tiktok_url = %s,
                x_url = %s,
                youtube_url = %s,
                bio = %s,
                show_profile_to_logged_in_users = %s,
                show_activity_on_profile = %s
            WHERE email = %s
            """,
            (
                payload["name"],
                payload["role"],
                payload["company"],
                payload["location"],
                payload["focus_area"],
                payload["website"],
                payload["headline"],
                payload["profile_picture"],
                payload["facebook_url"],
                payload["instagram_url"],
                payload["linkedin_url"],
                payload["tiktok_url"],
                payload["x_url"],
                payload["youtube_url"],
                payload["bio"],
                int(payload["show_profile_to_logged_in_users"]),
                int(payload["show_activity_on_profile"]),
                email,
            ),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def get_hydrated_user_by_email(email):
    user = get_user_by_email(email)
    return hydrate_user(user)
