import pytest
import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)
from src.parse_line import parse_csv_lines


def test_parse_csv_lines_valid_data():
    lines = ["New York, 30, Alice", "London, 25, Bob"]
    expected = [
        {"city": "New York", "age": 30, "name": "Alice"},
        {"city": "London", "age": 25, "name": "Bob"},
    ]
    assert parse_csv_lines(lines) == expected


def test_parse_csv_lines_invalid_age():
    lines = ["Paris, twenty-five, Charlie"]
    expected = [{"city": "Paris", "age": None, "name": "Charlie"}]
    assert parse_csv_lines(lines) == expected


def test_parse_csv_lines_incorrect_parts():
    lines = ["Berlin, 35"]
    expected = [{"city": None, "age": None, "name": None}]
    assert parse_csv_lines(lines) == expected


def test_parse_csv_lines_empty_input():
    lines = []
    expected = []
    assert parse_csv_lines(lines) == expected


def test_parse_csv_lines_mixed_valid_invalid():
    lines = [
        "Tokyo, 40, Dana",
        "Invalid Data",
        "Sydney, twenty, Eva",
        "Moscow, 22, Frank",
    ]
    expected = [
        {"city": "Tokyo", "age": 40, "name": "Dana"},
        {"city": None, "age": None, "name": None},
        {"city": "Sydney", "age": None, "name": "Eva"},
        {"city": "Moscow", "age": 22, "name": "Frank"},
    ]
    assert parse_csv_lines(lines) == expected
