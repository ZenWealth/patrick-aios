"""
CommandOS - Weekly GTD review reminder

Sends a Telegram message to the General topic reminding Patrick to run
/review. Scheduled via cron for Saturday mornings.

Usage:
    python3 scripts/send_review_reminder.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_env  # noqa: E402

try:
    import requests
except ImportError:
    raise ImportError("Missing 'requests' - run: pip install requests")

MESSAGE = (
    "Good morning! It's Saturday — time for your weekly GTD review.\n\n"
    "Open this chat and send /review when you're ready, or fold it into "
    "your goal-setting session this morning."
)


def main():
    token = get_env("TELEGRAM_BOT_TOKEN")
    group_id = get_env("TELEGRAM_GROUP_ID")

    if not token or not group_id:
        print("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_GROUP_ID in .env")
        sys.exit(1)

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, json={"chat_id": group_id, "text": MESSAGE}, timeout=15)

    if resp.status_code == 200:
        print("Review reminder sent.")
    else:
        print(f"Failed to send reminder: HTTP {resp.status_code} - {resp.text}")
        sys.exit(1)


if __name__ == "__main__":
    main()
