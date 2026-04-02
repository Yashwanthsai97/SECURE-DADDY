import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.db import init_db
from models.user_model import create_user, get_user_by_email

USERS_JSON_PATH = BASE_DIR / "users.json"


def main():
    if not USERS_JSON_PATH.exists():
        print("users.json not found, nothing to migrate.")
        return

    raw_users = json.loads(USERS_JSON_PATH.read_text(encoding="utf-8"))
    init_db()

    migrated_count = 0
    skipped_count = 0

    for email, user in raw_users.items():
        normalized_email = (email or user.get("email") or "").strip().lower()
        if not normalized_email:
            skipped_count += 1
            continue

        if get_user_by_email(normalized_email):
            skipped_count += 1
            continue

        create_user(
            name=(user.get("name") or "SecureDaddy User").strip(),
            email=normalized_email,
            username=(user.get("username") or normalized_email).strip().lower(),
            password_hash=user.get("password_hash") or "",
            password_algorithm="werkzeug",
            user_data={
                "role": user.get("role"),
                "company": user.get("company"),
                "location": user.get("location"),
                "focus_area": user.get("focus_area"),
                "bio": user.get("bio"),
                "website": user.get("website"),
                "headline": user.get("headline"),
                "profile_picture": user.get("profile_picture"),
                "facebook_url": user.get("facebook_url"),
                "instagram_url": user.get("instagram_url"),
                "linkedin_url": user.get("linkedin_url"),
                "tiktok_url": user.get("tiktok_url"),
                "x_url": user.get("x_url"),
                "youtube_url": user.get("youtube_url"),
                "show_profile_to_logged_in_users": user.get("show_profile_to_logged_in_users", True),
                "show_activity_on_profile": user.get("show_activity_on_profile", True),
                "created_at": user.get("created_at"),
                "last_login_at": user.get("last_login_at"),
            },
        )
        migrated_count += 1

    print(f"Migrated: {migrated_count}")
    print(f"Skipped: {skipped_count}")


if __name__ == "__main__":
    main()
