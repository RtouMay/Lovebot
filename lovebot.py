# lovebot.py
import logging, os, json, pytz, datetime, asyncio, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)

# -------------------- ENV --------------------
BOT_TOKEN        = os.getenv("BOT_TOKEN", "")
PARTNER_CHAT_ID  = int(os.getenv("PARTNER_CHAT_ID", "0"))  # پارتنرت
YOUR_CHAT_ID     = int(os.getenv("YOUR_CHAT_ID", "0"))     # خودت
HF_TOKEN         = os.getenv("HF_TOKEN", "")               # اختیاری برای AI
SEND_HOUR_IRAN   = int(os.getenv("SEND_HOUR_IRAN", "10"))  # ساعت ارسال 10 صبح ایران
CHECK_INTERVAL   = int(os.getenv("CHECK_INTERVAL", "30"))  # هر 30 ثانیه چک

IRAN_TZ = pytz.timezone("Asia/Tehran")
DB_FILE = "period_status.json"

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

# -------------------- DB --------------------
def load_status():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_status(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -------------------- پیام‌های پریودی --------------------
PERIOD_MESSAGES = [
    "قلبم 🩷 امروز هیچی ازت نمی‌خوام جز اینکه یه کوچولو بیشتر استراحت کنی. بدن نازت خسته‌ست، تاج سرمی تو، بذار یه کم نفس بکشی 😚",
    "دردت به جونم نفسم 😢 امروز اگه حالت گرفته‌ست، بدون من کنارت نفس می‌کشم. یه چای گرم بخور و بخند برام، ماه منی تو ❤️",
    "سقت بام عشقم 😘 امروز فقط می‌خوام بدونی قشنگ‌ترین آدم دنیایی، حتی وقتی رنگت پریده‌ست. فدات شم که اینقدر قوی‌ای 💪",
    "نفسم 💕 زیاد فکر نکن، یه آهنگ آروم گوش بده، پتوتو بپیچ دورت و بدون من همین الان دارم بهت فکر می‌کنم 😍",
    "فدات شم تاج سرم 👑 اگه دل‌درد داری، آروم بخواب، من همین‌جا کنارتم، کاش بودم بغل‌ت کنم 💞",
    "ماه من 🌙 روز شیشمه، یعنی دیگه تمومه قربون اون صبرت برم 😍 یه لبخند بزن که دلم قنج بره 😘",
    "امیدم 😍 آخ که نفس بکشم وقتی بدونم حالت خوب شده ❤️ تموم شد عشق من، از فردا فقط لبخند و خوشحالی باشه برام 😍"
]

# -------------------- UI --------------------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🩸 من پریود شدم", callback_data="period")],
        [InlineKeyboardButton("🤖 حرف زدن با هوش مصنوعی", callback_data="ai_chat")],
        [InlineKeyboardButton("💌 دلتنگتم", callback_data="miss_you")]
    ])

# -------------------- Handlers --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام نازنینم 🌸 من همیشه اینجام برای تو 💖\nیکی از گزینه‌ها رو بزن:",
        reply_markup=main_menu()
    )

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("منو:", reply_markup=main_menu())

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    status = load_status()

    if data == "period":
        today = datetime.datetime.now(IRAN_TZ).date().isoformat()
        status["period_start"] = today
        save_status(status)
        await query.message.reply_text(
            "مرسی که گفتی عزیز دلم 🩷 از امروز تا ۷ روز مراقبتت می‌کنم 😘",
            reply_markup=main_menu()
        )

    elif data == "ai_chat":
        status["ai_mode"] = True
        save_status(status)
        await query.message.reply_text("هرچی خواستی بپرس عشق من 😍 (برای خروج از حالت AI، /menu بزن)")

    elif data == "miss_you":
        text = "زهرا دلش برات تنگ شده 😍 زنگش بزن یا براش یه پیام بفرست 💞"
        try:
            requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                params={"chat_id": YOUR_CHAT_ID, "text": text}, timeout=10
            )
        except Exception as e:
            logging.info(f"Send to YOU failed: {e}")
        await query.message.reply_text("بهش گفتم که دلت تنگ شده 🥺❤️", reply_markup=main_menu())

async def ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = load_status()
    if not status.get("ai_mode"):
        return
    text = (update.message.text or "").strip()
    if not text:
        return
    if not HF_TOKEN:
        await update.message.reply_text("فعلاً هوش مصنوعی غیرفعاله 😅 /menu رو بزن برگردی به منو")
        return
    try:
        resp = requests.post(
            "https://api-inference.huggingface.co/models/gpt2",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": text, "options": {"wait_for_model": True}},
            timeout=30
        )
        data = resp.json()
        if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
            msg = data[0]["generated_text"]
        else:
            msg = str(data)
        await update.message.reply_text(msg[:700])
    except Exception:
        await update.message.reply_text("اوه مشکل پیش اومد، یه کم دیگه امتحان کن عشق من 🫶")

# -------------------- Daily loop --------------------
async def daily_check(app):
    while True:
        now = datetime.datetime.now(IRAN_TZ)
        if now.hour == SEND_HOUR_IRAN and now.minute < 1:
            status = load_status()
            if "period_start" in status:
                start_date = datetime.date.fromisoformat(status["period_start"])
                delta = (now.date() - start_date).days
                if 0 <= delta < 7:
                    msg = PERIOD_MESSAGES[delta]
                    try:
                        await app.bot.send_message(chat_id=PARTNER_CHAT_ID, text=msg)
                    except Exception as e:
                        logging.info(f"Send period msg failed: {e}")
                elif delta >= 7:
                    del status["period_start"]
                    save_status(status)
        await asyncio.sleep(CHECK_INTERVAL)

# -------------------- Boot --------------------
async def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN ست نشده!")
        return
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_message))
    asyncio.create_task(daily_check(app))
    print("💖 LoveBot is running…")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
