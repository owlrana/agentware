"""Hidden grader for feature-csv-parser task. Agent NEVER sees this file."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repo.csv_parser import parse_row


def test_empty_string():
    assert parse_row("") == []


def test_simple_fields():
    assert parse_row("a,b,c") == ["a", "b", "c"]


def test_whitespace_stripped():
    assert parse_row("  hello , world  , foo ") == ["hello", "world", "foo"]


def test_quoted_field_with_comma():
    assert parse_row('a,"b,c",d') == ["a", "b,c", "d"]


def test_quoted_field_preserves_whitespace():
    assert parse_row('" hello ",b') == [" hello ", "b"]


def test_escaped_quote():
    # Two double-quotes inside a quoted field = one literal quote
    assert parse_row('"say ""hi""",done') == ['say "hi"', "done"]


def test_mixed_fields():
    result = parse_row('name, "Smith, John" , 42')
    assert result == ["name", "Smith, John", "42"]


def test_single_field():
    assert parse_row("only") == ["only"]


def test_single_quoted_field():
    assert parse_row('"quoted"') == ["quoted"]


def test_empty_fields():
    assert parse_row(",, ") == ["", "", ""]
