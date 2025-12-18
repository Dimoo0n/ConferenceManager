import re
from datetime import datetime

def validate_group_name(name: str) -> bool:
    if not name:
        return False
    length = len(name)
    if 2 <= length <= 20 and re.match(r'^[\w-]+$', name):
        return True
    return False

def validate_conf_date(date_text: str) -> bool:
    try:
        input_date = datetime.strptime(date_text, '%d.%m.%Y')
        if input_date.date() < datetime.now().date():
            return False
        return True
    except ValueError:
        return False

def validate_url(url: str) -> bool:
    if not url:
        return False
    return url.startswith(("http://", "https://")) and len(url) > 10