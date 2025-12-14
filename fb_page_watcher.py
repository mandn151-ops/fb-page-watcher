import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import hashlib

# ====== CONFIG ======
PAGES = [
    "https://www.facebook.com/smartbuyjo",
    "https://www.facebook.com/MeccaMallJordan",
    "https://www.facebook.com/CityMallJo",
    "https://www.facebook.com/SafewayJo",
    "https://www.facebook.com/TAJLifestyleCenter",
    "https://www.facebook.com/yasermall.bros",
    "https://www.facebook.com/alfaridstores",
    "https://www.facebook.com/mce.mil.jo123",
    "https://www.facebook.com/official.jcscc",
    "https://www.facebook.com/ASQ.JO",
    "https://www.facebook.com/OceanFreshFish",
    "https://www.facebook.com/AlkarmelGroup",
    "https://www.facebook.com/mallcitystores",
    "https://www.facebook.com/Abuodehstores",
    "https://www.facebook.com/profile.php?id=61563710747862",
    "https://www.facebook.com/leaderscenterjo",
    "https://www.facebook.com/JaberStoresJor",
    "https://www.facebook.com/SahsehForOffers",
    "https://www.facebook.com/AlMutasaweqMarketJo",
    "https://www.facebook.com/Durra.Gallery.Aydun",
]

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

STATE_FILE = "state.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; fb-page-watcher/1.0)"
}

# ====== HELPERS ======
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": True
    }
    requests.post(url, json=payload, timeout=30)

def hash_key(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# ====== CORE ======
def check_page(page_url, state):
    try:
        r = requests.get(page_url, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        links = [a.get("href") for a in soup.find_all("a", href=True)]

        # ✅ صور فقط
        photo_links = [
            l for l in links
            if l and (
                "/photos/" in l or
                "photo.php" in l
            )
        ]

        if not photo_links:
            return None

        latest = photo_links[0]
        key = hash_key(page_url)

        if state.get(key) == latest:
            return None

        state[key] = latest

        page_name = page_url.replace("https://www.facebook.com/", "")
        return {
            "page": page_name,
            "link": latest
        }

    except Exception as e:
        print(f"Error checking {page_url}: {e}")
        return None

def main():
    state = load_state()
    results = []

    for page in PAGES:
        result = check_page(page, state)
        if result:
            results.append(result)

    if results:
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        message = "📸 صور جديدة على فيسبوك\n"
        message += f"🕒 {now}\n\n"

        for r in results:
            message += f"• {r['page']}\n{r['link']}\n\n"

        send_telegram(message)
        save_state(state)
        print(f"Sent {len(results)} updates")
    else:
        print("No new photos")

if __name__ == "__main__":
    main()
