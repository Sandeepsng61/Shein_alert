import requests
import re
import time
import logging
import threading
from typing import Dict
from flask import Flask

# === Configuration ===
BOT_TOKEN = "8329618002:AAFLi4Vsn-IQNdG9fplvMMQpx8UQ03VUm44"
CHAT_IDS = [
    2040231851,       # Personal chat
    -1003282279961    # Group chat
]
TARGET_URL = "https://www.sheinindia.in/c/sverse-5939-37961"
CHECK_INTERVAL = 30  # seconds

# === Logging Setup ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# === Telegram Send Function ===
def send_telegram_message(message: str) -> None:
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for chat_id in CHAT_IDS:
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        try:
            response = requests.post(telegram_url, data=payload, timeout=10)
            response.raise_for_status()
            logging.info(f"✅ Telegram alert sent to chat ID {chat_id}")
        except requests.RequestException as e:
            logging.error(f"❌ Failed to send Telegram message to {chat_id}: {e}")

# === Scraping Logic ===
def get_stock_counts() -> Dict[str, int]:
    try:
        response = requests.get(TARGET_URL, timeout=15)
        response.raise_for_status()
        html = response.text
        matches = re.findall(r'"genderfilter-(Women|Men)".*?"count":(\d+)', html)
        counts = {gender: int(count) for gender, count in matches}
        return counts
    except requests.RequestException as e:
        logging.error(f"🌐 Error fetching stock data: {e}")
        return {"Men": 0, "Women": 0}
    except Exception as e:
        logging.error(f"⚠️ Unexpected error while parsing stock data: {e}")
        return {"Men": 0, "Women": 0}

# === Monitor Thread ===
def monitor_stock():
    previous_counts = {"Men": 0, "Women": 0}
    logging.info("👀 Stock monitoring started... checking every %s seconds", CHECK_INTERVAL)

    while True:
        counts = get_stock_counts()
        men_stock = counts.get("Men", 0)
        women_stock = counts.get("Women", 0)
        total_stock = men_stock + women_stock
        logging.info(f"Checked stock — 👩 Women: {women_stock}, 👨 Men: {men_stock}, 🧮 Total: {total_stock}")

        # Detect changes
        if counts != previous_counts:
            msg_parts = []

            def diff_line(label: str, old: int, new: int) -> str:
                diff = new - old
                if diff > 0:
                    return f"{label}: <b>{new}</b> 🔼 (+{diff})"
                elif diff < 0:
                    return f"{label}: <b>{new}</b> 🔽 ({diff})"
                else:
                    return f"{label}: <b>{new}</b>"

            msg_parts.append(diff_line("👩 <b>Women</b>", previous_counts["Women"], women_stock))
            msg_parts.append(diff_line("👨 <b>Men</b>", previous_counts["Men"], men_stock))
            msg_parts.append(f"🧮 <b>Total Products:</b> <b>{total_stock}</b>")

            message = (
                "🛍️ <b>Shein Stock Update</b>\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                + "\n".join(msg_parts) + "\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                f"🔗 <a href='{TARGET_URL}'>View on Shein</a>\n"
                "⏰ Updated just now"
            )

            send_telegram_message(message)
            previous_counts = counts

        time.sleep(CHECK_INTERVAL)

# === Flask Keep-Alive Server ===
app = Flask(__name__)

@app.route('/')
def home():
    return "🟢 Shein alert bot is running successfully!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# === Main ===
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    monitor_stock()
