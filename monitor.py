import os
import re
import sys
import time
import requests
from bs4 import BeautifulSoup

URL = "https://srsmatha.org/srsmatha_tatkal/main_web/tatkal.php"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Polling configuration
INTERVAL_SECONDS = 10         # Check every 10 seconds
TOTAL_DURATION_MINUTES = 12   # Run for 12 minutes (e.g., 5:55 AM to 6:07 AM IST)
MAX_ITERATIONS = int((TOTAL_DURATION_MINUTES * 60) / INTERVAL_SECONDS)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def send_alert(message: str) -> bool:
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.", file=sys.stderr)
        return False

    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        res = requests.post(telegram_url, json=payload, timeout=10)
        res.raise_for_status()
        print("Alert successfully pushed to Telegram!")
        return True
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}", file=sys.stderr)
        return False

def check_portal(session: requests.Session) -> bool:
    """Returns True if an open slot is detected, False otherwise."""
    try:
        response = session.get(URL, headers=HEADERS, timeout=8)
        if response.status_code != 200:
            print(f"[{time.strftime('%X')}] HTTP {response.status_code}")
            return False

        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text(separator=" ", strip=True)

        # Look for availability patterns (e.g., "6 Tatkal options available" or "Book Now")
        slot_match = re.search(r"(\d+)\s+Tatkal options available", page_text, re.IGNORECASE)
        has_general_slot = "Tatkal options available" in page_text or "Book Now" in page_text

        if slot_match or has_general_slot:
            matched_info = slot_match.group(0) if slot_match else "Available slots detected"
            print(f"[{time.strftime('%X')}] Slot found: {matched_info}")

            alert_body = (
                "🚨 <b>SRS Matha Tatkal Room Open!</b>\n\n"
                f"<b>Status:</b> {matched_info}\n\n"
                f'👉 <a href="{URL}">Open Booking Portal Now</a>'
            )
            send_alert(alert_body)
            return True

        print(f"[{time.strftime('%X')}] No slots open yet (All dates sold out or unreleased).")
        return False

    except requests.RequestException as err:
        print(f"[{time.strftime('%X')}] Connection error: {err}")
        return False

def main():
    print(f"Starting monitor: polling every {INTERVAL_SECONDS}s for {TOTAL_DURATION_MINUTES} mins...")

    with requests.Session() as session:
        for iteration in range(1, MAX_ITERATIONS + 1):
            if check_portal(session):
                print("Slot detected and alert sent. Stopping monitor.")
                sys.exit(0)

            time.sleep(INTERVAL_SECONDS)

    print("Monitoring window completed without detecting released slots.")

if __name__ == "__main__":
    main()
