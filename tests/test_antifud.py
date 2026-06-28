import pytest
from filters.antifud import contains_fud

def test_detects_fud_keyword():
    keywords = ["rug", "scam", "dead"]
    assert contains_fud("this is a rug pull", keywords) is True

def test_case_insensitive_detection():
    keywords = ["scam"]
    assert contains_fud("This is a SCAM project", keywords) is True

def test_no_fud_in_clean_message():
    keywords = ["rug", "scam"]
    assert contains_fud("I love kekcoin WAGMI", keywords) is False

def test_partial_match():
    keywords = ["rug"]
    assert contains_fud("this will rugpull us", keywords) is True
