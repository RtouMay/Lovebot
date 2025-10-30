# app.py
from flask import Flask
import threading
import time
import requests
import random
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# -------- تنظیمات (از Env می‌خونه) --------
BOT_TOKEN = os.environ.get("BOT_TOKEN")            # مقدار رو در Render قرار بده
CHAT_ID = int(os.environ.get("CHAT_ID", "0"))     # مقدار عددی (int)
HF_API_KEY = os.environ.get("HF_API_KEY")         # HuggingFace token
SEND_HOUR_IRAN = int(os.environ.get("SEND_HOUR_IRAN", "10"))  # ساعت ارسال به وقت ایران
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "60")) # بررسی هر چند ثانیه برای ارسال (داخل loop)

# -------- تنظیمات HF Inference --------
HF_API_URL = "https://api-inference.huggingface.co/models/gpt2"  # یا مدل دیگه که خواستی
HF_HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"} if HF_API_KEY else {}

# -------- timezone ایران --------
IRAN_TZ = pytz.timezone("Asia/Tehran")

# -------- توابع --------
def generate_love_message():
    """یک متن کوتاه عاشقانه تولید می‌کند (fallback ساده هم دارد)."""
    prompts = [
        "یه پیام کوتاه و خودمونی عاشقانه به فارسی بنویس، صمیمی و ناز:",
        "جمله‌ای خیلی لطیف و عاشقانه برای دوست دخترم به فارسی بنویس:",
        "متن کوتاه و خاص و عاشقانه، خودمونی و رومانتیک:"
    ]
    prompt = random.choice(prompts)
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}
    try:
        r = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        # فرمت پاسخ ممکنه بین مدل‌ها فرق کنه؛
        # اگر پاسخ array از نوع {"generated_text": "..."} باشه:
        if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
            text = data[0]["generated_text"]
        # برخی inference ها متن را مستقیم در یک فیلد دیگر دارند — ساده fallback:
        elif isinstance(data, dict) and "generated_text" in data:
            text = data["generated_text"]
        else:
            # تلاش برای استخراج متن از رشته‌ی JSON یا موارد دیگر
            text = str(data)
        text = text.strip().replace("\n", " ")
        # محدودیت طول پیام
        return (text[:450] + "...") if len(text) > 450 else text
    except Exception as e:
        print("⚠️ HF generate error:", e, flush=True)
        # fallback پیام آماده
        fallback = [
            "عشق منی؛ همیشه یادتم 💖",
            "صبحت بخیر عشقم، دلم برات تنگه 😘",
            "قربونت برم، امروز هم بهترینِ منی 💫"
        ]
        return random.choice(fallback)

def send_message(text):
    """ارسال پیام به تلگرام"""
    if not BOT_TOKEN or CHAT_ID == 0:
        print("❌ BOT_TOKEN یا CHAT_ID تنظیم نشده", flush=True)
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        r = requests.post(url, data=payload, timeout=15)
        r.raise_for_status()
        print("✅ Message sent successfully.", flush=True)
        return True
    except Exception as e:
        print("❌ Telegram send error:", e, flush=True)
        return False

def is_time_to_send():
    """بررسی می‌کند الان وقت ارسال پیام به وقت ایران هست یا نه."""
    now = datetime.now(IRAN_TZ)
    # ارسال دقیق در دقیقه صفر ساعت مشخص
    return now.hour == SEND_HOUR_IRAN and now.minute == 0

def daily_loop():
    """لوپ پس‌زمینه که هر روز ساعت مشخص پیام می‌فرستد."""
    print("🔄 Daily loop started", flush=True)
    sent_today = False
    while True:
        try:
            if is_time_to_send():
                if not sent_today:
                    msg = generate_love_message()
                    send_message(msg)
                    sent_today = True
                else:
                    # قبلاً امروز فرستاده شده، منتظر بمان تا ساعت از محدوده خارج شود
                    pass
            else:
                # وقتی ساعت رفت به غیر از زمان ارسال، flag رو ریست کن
                if sent_today:
                    sent_today = False
        except Exception as e:
            print("⚠️ Error in daily loop:", e, flush=True)
        time.sleep(CHECK_INTERVAL)

# -------- Flask routes برای تست --------
@app.route("/")
def home():
    return "<h3>✅ Love-bot alive</h3>", 200

@app.route("/test_send")
def test_send_route():
    """با باز کردن این آدرس یک پیام تست برای CHAT_ID ارسال می‌شود."""
    text = generate_love_message()
    ok = send_message(text)
    return ("✅ Test message sent" if ok else "❌ Test failed; check logs"), 200

@app.route("/keep_alive")
def keep_alive():
    return "✅ Bot is alive!", 200

# -------- شروع ترد و اجرای Flask --------
if __name__ == "__main__":
    # ترد ارسال روزانه را راه‌اندازی کن
    t = threading.Thread(target=daily_loop, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
