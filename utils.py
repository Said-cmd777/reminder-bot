
from datetime import datetime
import logging

CANCEL_TEXT = "إلغاء"
CANCEL_TEXT_ALIASES = (CANCEL_TEXT, "الغاء", "cancel")

def init_logging(log_file):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def parse_dt(dt_str):
    
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

def is_cancel_text(text):
    if not text:
        return False
    return text.strip().lower() in CANCEL_TEXT_ALIASES
