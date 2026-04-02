from flask import jsonify, request, session

from models.user_model import get_hydrated_user_by_email, get_user_by_email, update_profile
from utils.profile import DEFAULT_PROFILE_VALUES, profile_completion_score


def save_profile():
    user_email = session.get("user_email")
    if not user_email:
        return jsonify({"error": "You must be signed in to update your profile."}), 401

    user = get_user_by_email(user_email)
    if not user:
        return jsonify({"error": "Account not found."}), 404

    payload = request.get_json(silent=True) or {}
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

    for key, value in list(updated_fields.items()):
        updated_fields[key] = value if value else DEFAULT_PROFILE_VALUES.get(key, "")

    updated_fields["show_profile_to_logged_in_users"] = bool(
        payload.get("show_profile_to_logged_in_users", True)
    )
    updated_fields["show_activity_on_profile"] = bool(
        payload.get("show_activity_on_profile", True)
    )

    update_profile(user_email, updated_fields)
    hydrated_user = get_hydrated_user_by_email(user_email)

    return jsonify(
        {
            "message": "Profile updated successfully.",
            "user": hydrated_user,
            "completion_score": profile_completion_score(hydrated_user),
        }
    )
