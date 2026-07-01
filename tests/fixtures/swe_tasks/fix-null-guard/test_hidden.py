"""Hidden grader for fix-null-guard task. Agent NEVER sees this file."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repo.users import find_user, find_users_by_domain

USERS = [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@test.org"},
    {"name": "Ghost", "email": None},
    {"name": "Carol", "email": "carol@example.com"},
]


def test_find_user_normal():
    result = find_user(USERS, "Alice@Example.com")
    assert result is not None
    assert result["name"] == "Alice"


def test_find_user_not_found():
    assert find_user(USERS, "nobody@x.com") is None


def test_find_user_none_email():
    """Must not crash when search email is None."""
    assert find_user(USERS, None) is None


def test_find_user_skips_none_entries():
    """Must not crash when a user dict has email=None."""
    result = find_user(USERS, "carol@example.com")
    assert result is not None
    assert result["name"] == "Carol"


def test_find_users_by_domain_normal():
    result = find_users_by_domain(USERS, "example.com")
    names = [u["name"] for u in result]
    assert "Alice" in names
    assert "Carol" in names
    assert "Bob" not in names


def test_find_users_by_domain_skips_none():
    """Must not crash when iterating users with None email."""
    result = find_users_by_domain(USERS, "test.org")
    assert len(result) == 1
    assert result[0]["name"] == "Bob"
