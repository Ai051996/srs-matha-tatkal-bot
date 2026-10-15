import os
import re
import sys
import time
import requests
from playwright.sync_api import sync_playwright

URL = "https://srsmatha.org/srsmatha_tatkal/main_web/tatkal.php"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

INTERVAL_SECONDS = 10
TOTAL_DURATION_MINUTES = 12
MAX_ITERATIONS = int((TOTAL_DURATION_MINUTES * 60) / INTERVAL_SECONDS)

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
        print(">>> Alert successfully sent to Telegram! <<<")
        return True
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}", file=sys.stderr)
        return False

def check_portal(page) -> bool:
    try:
        page.goto(URL, wait_until="networkidle", timeout=15000)
        
        # Wait until the dynamic JS finishes replacing the loading placeholder
        try:
            page.wait_for_function(
                "() => !document.body.innerText.includes('Fetching Tatkal availability')",
                timeout=8000
            )
        except Exception:
            pass # Continue to evaluate even if it times out

        body_text = page.inner_text("body")
        clean_text = " ".join(body_text.split())

        # Check for slot numbers (e.g., '5 Tatkal options available')
        slot_matches = re.findall(r"(\d+)\s*Tatkal options available", clean_text, re.IGNORECASE)

        if slot_matches:
            count = slot_matches[0]
            print(f"[{time.strftime('%X')}] AVAILABLE: Found {count} Tatkal options!")
            alert_body = (
                f"🚨 <b>SRS Matha Tatkal Room Open!</b>\n\n"
                f"<b>Available:</b> {count} Tatkal options\n\n"
                f'👉 <a href="{URL}">Open Booking Portal Now</a>'
            )
            return send_alert(alert_body)

        print(f"[{time.strftime('%X')}] Fully sold out / no slots currently open.")
        return False

    except Exception as err:
        print(f"[{time.strftime('%X')}] Page check error: {err}")
        return False

def main():
    print(f"Starting browser monitor: polling every {INTERVAL_SECONDS}s...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for iteration in range(1, MAX_ITERATIONS + 1):
            if check_portal(page):
                print("Slot found and alert sent. Terminating.")
                browser.close()
                sys.exit(0)

            time.sleep(INTERVAL_SECONDS)

        browser.close()

    print("Finished monitoring window.")

if __name__ == "__main__":
    main()
