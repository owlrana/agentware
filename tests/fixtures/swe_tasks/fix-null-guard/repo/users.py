"""User lookup utilities."""


def find_user(users, email):
    """Find a user dict by email (case-insensitive match).

    Args:
        users: List of user dicts, each with an 'email' key.
        email: The email to search for.

    Returns:
        The matching user dict, or None if not found.
    """
    normalized = email.lower()  # BUG: crashes when email is None
    for user in users:
        if user["email"].lower() == normalized:  # BUG: crashes when user email is None
            return user
    return None


def find_users_by_domain(users, domain):
    """Return all users whose email ends with the given domain."""
    result = []
    for user in users:
        if user["email"].endswith("@" + domain):  # BUG: crashes on None email
            result.append(user)
    return result
