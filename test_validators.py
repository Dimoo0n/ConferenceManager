import pytest
from datetime import datetime, timedelta
from validators import validate_group_name, validate_conf_date, validate_url

def test_group_name_valid():
    assert validate_group_name("Java-Pro") is True
    assert validate_group_name("G-1") is True

def test_group_name_too_short():
    assert validate_group_name("A") is False

def test_group_name_too_long():
    long_name = "A" * 21
    assert validate_group_name(long_name) is False

def test_group_name_invalid_chars():
    assert validate_group_name("Group$") is False
    assert validate_group_name("Hello World") is False

def test_date_valid_future():
    future_date = (datetime.now() + timedelta(days=5)).strftime('%d.%m.%Y')
    assert validate_conf_date(future_date) is True

def test_date_valid_today():
    today = datetime.now().strftime('%d.%m.%Y')
    assert validate_conf_date(today) is True

def test_date_invalid_past():
    past_date = (datetime.now() - timedelta(days=1)).strftime('%d.%m.%Y')
    assert validate_conf_date(past_date) is False

def test_date_invalid_format():
    assert validate_conf_date("2025/12/01") is False
    assert validate_conf_date("32.01.2025") is False

def test_url_valid():
    assert validate_url("https://zoom.us/j/12345") is True
    assert validate_url("http://google.com") is True

def test_url_invalid_protocol():
    assert validate_url("ftp://files.com") is False
    assert validate_url("zoom.us/meeting") is False

def test_url_too_short():
    assert validate_url("https://") is False
