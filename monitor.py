import os
import sys
import time
import requests
from bs4 import BeautifulSoup

URL = "https://srsmatha.org/srsmatha_tatkal/main_web/tatkal.php"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Polling configuration
INTERVAL_SECONDS = 10        # Poll every 10 seconds
TOTAL_DURATION_MINUTES = 12  # Run for 12 minutes (e.g., 5:55 AM to 6:07 AM IST)
MAX_ITERATIONS = int((TOTAL_DURATION_MINUTES * 60) / INTERVAL_SECONDS)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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
    """Returns True if a slot is detected, False otherwise."""
    try:
        response = session.get(URL, headers=HEADERS, timeout=8)
        if response.status_code != 200:
            print(f"[{time.strftime('%X')}] HTTP {response.status_code}")
            return False

        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text()

        # Adjust keywords according to the specific active portal text
        is_available = ("Available" in page_text or "Book Now" in page_text) and "Fully sold out" not in page_text

        if is_available:
            print(f"[{time.strftime('%X')}] Available slot found!")
            alert_body = (
                "🚨 <b>SRS Matha Tatkal Room Open!</b>\n\n"
                "A booking slot was just detected!\n\n"
                f'<a href="{URL}">Open Booking Portal Now</a>'
            )
            send_alert(alert_body)
            return True

        print(f"[{time.strftime('%X')}] No slots yet (Status: Sold out / Not released).")
        return False

    except requests.RequestException as err:
        print(f"[{time.strftime('%X')}] Request failed: {err}")
        return False

def main():
    print(f"Starting monitor loop: checking every {INTERVAL_SECONDS}s for up to {TOTAL_DURATION_MINUTES} mins...")
    
    # Reusing a Session keeps the TCP/TLS connection warm and reduces request latency
    with requests.Session() as session:
        for iteration in range(1, MAX_ITERATIONS + 1):
            slot_found = check_portal(session)
            if slot_found:
                print("Slot detected and alert sent. Exiting cleanly.")
                sys.exit(0)

            time.sleep(INTERVAL_SECONDS)

    print("Monitoring window completed without finding open slots.")

if __name__ == "__main__":
    main()