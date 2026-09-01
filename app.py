import os
import re
import time
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TARGET_URL = "https://www.osmania.ac.in/examination-results.php"
CHECK_INTERVAL_SECONDS = 45

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def check_results():
    try:
        response = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return False
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"Fetch error: {e}")
        return False

    for row in soup.find_all("tr")[:20]:
        text = row.get_text(separator=" ", strip=True)
        lower_text = text.lower()
        
        has_bsc = "b.sc" in lower_text and "health care" not in lower_text
        has_rv = "rv" in lower_text or "revaluation" in lower_text
        has_sem = bool(re.search(r'\b(vi|sem-iv & vi|sem-vi)\b', lower_text))
        has_session = "2026" in lower_text or "may" in lower_text
        
        if has_bsc and has_rv and has_sem and has_session:
            link = row.find("a")
            href = link.get("href") if link else ""
            full_link = f"https://www.osmania.ac.in{href}" if href.startswith("/") else href
            
            msg = f"🔔 OU B.Sc Sem VI RV Out!\n\n{text}\n\nLink: {full_link}"
            for i in range(1, 4):
                send_telegram_alert(f"[ALERT {i}/3]\n{msg}")
                time.sleep(1)
            return True
            
    return False

def bot_loop():
    print("Background monitoring thread started...")
    send_telegram_alert("🚀 OU Result Bot is running on Render (Free)!")
    while True:
        if check_results():
            break
        time.sleep(CHECK_INTERVAL_SECONDS)

# Run the scraper loop in a background thread
threading.Thread(target=bot_loop, daemon=True).start()

@app.route("/")
def home():
    return "OU Result Bot is running active."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))