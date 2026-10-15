import os
import re
import sys
import time
import requests
from bs4 import BeautifulSoup

URL = "https://srsmatha.org/srsmatha_tatkal/main_web/tatkal.php"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

INTERVAL_SECONDS = 10
TOTAL_DURATION_MINUTES = 12
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
        print("[ERROR] Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID secrets!", file=sys.stderr)
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
        print(">>> Alert successfully sent to Telegram! <<<")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram alert: {e}", file=sys.stderr)
        return False

def check_portal(session: requests.Session) -> bool:
    try:
        # Step A: Hit the base portal first to acquire session cookie
        session.get("https://srsmatha.org/", headers=HEADERS, timeout=5)

        # Step B: Request the tatkal page
        response = session.get(URL, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        clean_text = " ".join(soup.get_text().split())

        # Check for numbers before "Tatkal options available"
        slot_matches = re.findall(r"(\d+)\s*Tatkal options available", clean_text, re.IGNORECASE)

        if slot_matches:
            total_slots = slot_matches[0]
            print(f"[{time.strftime('%X')}] FOUND: {total_slots} slots available!")
            
            alert_body = (
                f"🚨 <b>SRS Matha Tatkal Room Open!</b>\n\n"
                f"<b>Available:</b> {total_slots} options\n\n"
                f'👉 <a href="{URL}">Tap to Open Portal Immediately</a>'
            )
            return send_alert(alert_body)

        # Debug print: Show exactly what text the runner is reading
        print(f"[{time.strftime('%X')}] No slots found. Text snippet seen by runner:")
        # Print lines mentioning 'sold out' or 'available'
        for line in clean_text.split(". "):
            if any(k in line.lower() for k in ["sold out", "available", "tatkal", "released"]):
                print(f"   -> {line.strip()}")
        return False

    except Exception as err:
        print(f"Error: {err}")
        return False

def main():
    print(f"Starting monitor: polling every {INTERVAL_SECONDS}s for {TOTAL_DURATION_MINUTES} mins...")

    # Immediate verification of Telegram credentials on startup
    if not BOT_TOKEN or not CHAT_ID:
        print("WARNING: Bot token or Chat ID is not set. Alerts will fail.", file=sys.stderr)

    with requests.Session() as session:
        for iteration in range(1, MAX_ITERATIONS + 1):
            if check_portal(session):
                print("Alert dispatched. Stopping workflow.")
                sys.exit(0)

            time.sleep(INTERVAL_SECONDS)

    print("Finished polling cycle without finding open slots.")

if __name__ == "__main__":
    main()
