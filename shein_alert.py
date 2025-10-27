import requests
import re
import time
import logging
from typing import Dict

# === Configuration ===
BOT_TOKEN = "8329618002:AAFLi4Vsn-IQNdG9fplvMMQpx8UQ03VUm44"
CHAT_IDS = [
    2040231851,      # Your personal chat
    -1003282279961       # Your group chat
]
TARGET_URL = "https://www.sheinindia.in/c/sverse-5939-37961"
CHECK_INTERVAL = 30  # in seconds

# === Logging Setup ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# === Functions ===
def send_telegram_message(message: str) -> None:
    """Send a message to all configured Telegram chats."""
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for chat_id in CHAT_IDS:
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            response = requests.post(telegram_url, data=payload, timeout=10)
            response.raise_for_status()
            logging.info(f"Telegram alert sent to chat ID {chat_id}")
        except requests.RequestException as e:
            logging.error(f"Failed to send Telegram message to {chat_id}: {e}")

def get_stock_counts() -> Dict[str, int]:
    """Fetch current stock counts for Men and Women from the target page."""
    try:
        response = requests.get(TARGET_URL, timeout=15)
        response.raise_for_status()
        html = response.text
        matches = re.findall(r'"genderfilter-(Women|Men)".*?"count":(\d+)', html)
        counts = {gender: int(count) for gender, count in matches}
        return counts
    except requests.RequestException as e:
        logging.error(f"Error fetching stock data: {e}")
        return {"Men": 0, "Women": 0}
    except Exception as e:
        logging.error(f"Unexpected error while parsing stock data: {e}")
        return {"Men": 0, "Women": 0}

def format_stock_message(men_stock: int, women_stock: int) -> str:
    """Format the Telegram message for stock alert."""
    return (
        "🎉 <b>Stock Available Now!</b>\n\n"
        f"👩 Women: <b>{women_stock}</b>\n"
        f"👨 Men: <b>{men_stock}</b>\n\n"
        f"🛒 <a href='{TARGET_URL}'>Check Now</a>"
    )

# === Main Monitoring Logic ===
def monitor_stock():
    previous_in_stock = False
    logging.info("👀 Stock monitoring started... checking every %s seconds", CHECK_INTERVAL)

    while True:
        counts = get_stock_counts()
        men_stock = counts.get("Men", 0)
        women_stock = counts.get("Women", 0)
        logging.info(f"Checked stock — 👨 Men: {men_stock}, 👩 Women: {women_stock}")

        in_stock_now = men_stock > 0 or women_stock > 0

        # Send alert only when stock appears
        if in_stock_now and not previous_in_stock:
            message = format_stock_message(men_stock, women_stock)
            send_telegram_message(message)
            previous_in_stock = True

        # Reset flag when stock goes out of stock
        elif not in_stock_now and previous_in_stock:
            logging.warning("⚠️ Stock went out of stock again.")
            previous_in_stock = False

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor_stock()
