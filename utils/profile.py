from datetime import datetime, timedelta, timezone


IST = timezone(timedelta(hours=5, minutes=30))

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
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        parsed = parsed.astimezone(IST)
        return parsed.strftime("%d %b %Y, %I:%M %p IST")
    except ValueError:
        return str(value)


def hydrate_user(user):
    if not user:
        return None

    enriched_user = {**DEFAULT_PROFILE_VALUES, **user}
    enriched_user["name"] = (enriched_user.get("name") or "SecureDaddy User").strip()
    enriched_user["email"] = (enriched_user.get("email") or "").strip().lower()
    enriched_user["company"] = (
        enriched_user.get("company") or DEFAULT_PROFILE_VALUES["company"]
    ).strip()
    enriched_user["location"] = (
        enriched_user.get("location") or DEFAULT_PROFILE_VALUES["location"]
    ).strip()
    enriched_user["role"] = (enriched_user.get("role") or DEFAULT_PROFILE_VALUES["role"]).strip()
    enriched_user["focus_area"] = (
        enriched_user.get("focus_area") or DEFAULT_PROFILE_VALUES["focus_area"]
    ).strip()
    enriched_user["bio"] = (enriched_user.get("bio") or DEFAULT_PROFILE_VALUES["bio"]).strip()
    enriched_user["headline"] = (
        enriched_user.get("headline") or DEFAULT_PROFILE_VALUES["headline"]
    ).strip()
    enriched_user["website"] = (enriched_user.get("website") or "").strip()
    enriched_user["profile_picture"] = (enriched_user.get("profile_picture") or "").strip()
    enriched_user["facebook_url"] = (enriched_user.get("facebook_url") or "").strip()
    enriched_user["instagram_url"] = (enriched_user.get("instagram_url") or "").strip()
    enriched_user["linkedin_url"] = (enriched_user.get("linkedin_url") or "").strip()
    enriched_user["tiktok_url"] = (enriched_user.get("tiktok_url") or "").strip()
    enriched_user["x_url"] = (enriched_user.get("x_url") or "").strip()
    enriched_user["youtube_url"] = (enriched_user.get("youtube_url") or "").strip()
    enriched_user["show_profile_to_logged_in_users"] = bool(
        enriched_user.get("show_profile_to_logged_in_users", True)
    )
    enriched_user["show_activity_on_profile"] = bool(
        enriched_user.get("show_activity_on_profile", True)
    )
    enriched_user["initials"] = (
        "".join(part[0].upper() for part in enriched_user["name"].split() if part)[:2] or "SD"
    )
    enriched_user["created_at_display"] = format_profile_timestamp(
        enriched_user.get("created_at") or enriched_user.get("last_login_at")
    )
    enriched_user["last_login_at_display"] = format_profile_timestamp(
        enriched_user.get("last_login_at")
    )
    return enriched_user


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
