import bcrypt
from werkzeug.security import check_password_hash


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password, stored_password, password_algorithm):
    if password_algorithm == "bcrypt":
        is_valid = bcrypt.checkpw(
            plain_password.encode("utf-8"),
            stored_password.encode("utf-8"),
        )
        return is_valid, False

    if password_algorithm == "werkzeug":
        is_valid = check_password_hash(stored_password, plain_password)
        return is_valid, is_valid

    return False, False
