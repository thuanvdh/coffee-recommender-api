import re
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

def is_shop_open_now(opening_hours_str: Optional[str]) -> bool:
    """
    Checks if a shop is currently open based on its opening hours string.
    Expected format: "07:00 - 22:00"
    """
    # If no string or '24/7' or unparseable, default to True (open) or handle specifically. 
    # For now, if it's "24/7" or empty, treat it as open.
    if not opening_hours_str or opening_hours_str.strip() == "":
        return True
    
    if "24/7" in opening_hours_str:
        return True

    parts = opening_hours_str.split('-')
    if len(parts) != 2:
        return True

    start_str = parts[0].strip()
    end_str = parts[1].strip()

    time_pattern = r"^(\d{1,2}):(\d{2})$"
    start_match = re.match(time_pattern, start_str)
    end_match = re.match(time_pattern, end_str)

    if not start_match or not end_match:
        return True

    start_h = int(start_match.group(1))
    start_m = int(start_match.group(2))
    end_h = int(end_match.group(1))
    end_m = int(end_match.group(2))

    vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now = datetime.now(vn_tz)

    current_h = now.hour
    current_m = now.minute

    # normalize 24 to 0 if exists
    if current_h == 24:
        current_h = 0
    if start_h == 24:
        start_h = 0
    if end_h == 24:
        end_h = 0

    current_minutes = current_h * 60 + current_m
    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m

    if start_minutes <= end_minutes:
        # standard case, e.g. 07:00 - 22:00
        return start_minutes <= current_minutes <= end_minutes
    else:
        # overnight case, e.g. 18:00 - 02:00
        return current_minutes >= start_minutes or current_minutes <= end_minutes
