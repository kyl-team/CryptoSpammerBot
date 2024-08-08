from datetime import datetime


def format_date() -> str:
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")
