import requests
import re
import time

# === Telegram Config ===
BOT_TOKEN = "8329618002:AAFLi4Vsn-IQNdG9fplvMMQpx8UQ03VUm44"
CHAT_ID = "2040231851"

# === Target URL ===
url = "https://www.sheinindia.in/c/sverse-5939-37961"

# === Function to send Telegram message ===
def send_telegram_message(message):
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(telegram_url, data=payload, timeout=10)
        print("✅ Telegram alert sent!")
    except Exception as e:
        print("⚠️ Failed to send Telegram message:", e)

# === Function to get current stock counts ===
def get_stock_counts():
    response = requests.get(url, timeout=15)
    html = response.text
    matches = re.findall(r'"genderfilter-(Women|Men)".*?"count":(\d+)', html)
    counts = {gender: int(count) for gender, count in matches}
    return counts

# === Main logic ===
previous_in_stock = False  # track whether stock was previously available

print("👀 Monitoring started... checking every 30 sec")

while True:
    try:
        counts = get_stock_counts()
        men_stock = counts.get('Men', 0)
        women_stock = counts.get('Women', 0)

        print(f"Checked — 👨 Men: {men_stock}, 👩 Women: {women_stock}")

        in_stock_now = (men_stock > 0 or women_stock > 0)

        # Send alert only when stock appears (previously 0 and now available)
        if in_stock_now and not previous_in_stock:
            msg = (
                "🎉 <b>Stock Available Now!</b>\n\n"
                f"👩 Women: <b>{women_stock}</b>\n"
                f"👨 Men: <b>{men_stock}</b>\n\n"
                "🛒 <a href='https://www.sheinindia.in/c/sverse-5939-37961'>Check Now</a>"
            )
            send_telegram_message(msg)
            previous_in_stock = True

        # Reset when stock goes out of stock again
        elif not in_stock_now and previous_in_stock:
            print("⚠️ Stock went out of stock again.")
            previous_in_stock = False

    except Exception as e:
        print("⚠️ Error fetching data:", e)

    time.sleep(30)