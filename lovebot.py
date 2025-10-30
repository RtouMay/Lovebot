import os
import asyncio
import random
import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import requests

# گرفتن توکن‌ها از متغیرهای محیطی
BOT_TOKEN = os.getenv("BOT_TOKEN")
PARTNER_CHAT_ID = int(os.getenv("PARTNER_CHAT_ID"))
YOUR_CHAT_ID = int(os.getenv("YOUR_CHAT_ID"))
HF_TOKEN = os.getenv("HF_TOKEN")

# ساعت ارسال روزانه به وقت ایران
SEND_HOUR_IRAN = int(os.getenv("SEND_HOUR_IRAN", 10))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 30))

# دیتای موقت برای حالت پریود
period_start = None

# پیام‌های عاشقانه برای حالت پریود
period_messages = [
    "عشق من ❤️ بدونی که این روزا فقط آروم باش... من همیشه کنارتم تاج سرم 🥺💋",
    "قلبم 😘 دردت به جونم، سعی کن استراحت کنی و زیاد خودتو اذیت نکنی 🩷",
    "نفسم، یه لیوان چای بخور و فیلمی که دوست داری رو ببین 🎬 من هواتو دارم ❤️",
    "سقت بام عزیز دلم 😍 این چند روزم مثل همیشه باهم ردش می‌کنیم 💪"
]

# پیام‌های صبح عاشقانه
love_messages = [
    "صبح بخیر عشقم 😘 امروز هم مثل همیشه دلم فقط با یاد تو آروم میشه 💞",
    "قلبم 💖 امیدوارم روزت پر از حس خوب و آرامش باشه 🌸",
    "نفسم 😍 فقط خواستم یادت بندازم چقدر برام خاصی 😚",
    "دردت به جونم 💋 همیشه بخند چون دلم می‌خواد لبخندتو ببینه 🌞",
    "فدات شم تاج سرم 💞 بدون تو این دنیا هیچ معنی‌ای نداره 😍"
]

# ساخت کیبورد منو اصلی
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🩸 پریود شدم", callback_data="period")],
        [InlineKeyboardButton("🤖 حرف زدن با هوش مصنوعی", callback_data="ai")],
        [InlineKeyboardButton("💌 دلتنگتم", callback_data="missing")]
    ]
    return InlineKeyboardMarkup(keyboard)

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام عشق من 💖\nمن اینجام تا هر روز حالت رو بهتر کنم 😍\nیه گزینه رو انتخاب کن:",
        reply_markup=main_menu()
    )

# هندلر دکمه‌ها
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global period_start
    query = update.callback_query
    await query.answer()

    if query.data == "period":
        period_start = datetime.datetime.now(pytz.timezone("Asia/Tehran"))
        await query.edit_message_text("❤️ فهمیدم عشقم، از امروز تا ۷ روز مراقبتت می‌کنم 😘")
    elif query.data == "ai":
        await query.edit_message_text("بنویس عشقم 🌸 چی می‌خوای ازم بپرسی؟ (فعلاً بخش هوش مصنوعی آزمایشی‌ه)")
    elif query.data == "missing":
        await context.bot.send_message(
            chat_id=YOUR_CHAT_ID,
            text="💌 زهرا دلش برات تنگ شده 😢 وقتشه بهش پیام بدی یا زنگ بزنی ❤️"
        )
        await query.edit_message_text("فدات شم 😍 بهش گفتم که دلت تنگ شده 💞")

# تابع ارسال پیام پریود
async def send_period_message(app):
    global period_start
    if not period_start:
        return
    now = datetime.datetime.now(pytz.timezone("Asia/Tehran"))
    if (now - period_start).days < 7:
        msg = random.choice(period_messages)
        await app.bot.send_message(chat_id=PARTNER_CHAT_ID, text=msg)
    else:
        period_start = None

# ارسال پیام صبح
async def send_daily_love(app):
    iran = pytz.timezone("Asia/Tehran")
    now = datetime.datetime.now(iran)
    if now.hour == SEND_HOUR_IRAN:
        msg = random.choice(love_messages)
        await app.bot.send_message(chat_id=PARTNER_CHAT_ID, text=msg)

# حلقه بررسی و ارسال خودکار
async def scheduler(app):
    while True:
        await send_period_message(app)
        await send_daily_love(app)
        await asyncio.sleep(CHECK_INTERVAL * 60)

# اجرای اصلی
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("💖 LoveBot is running…")
    asyncio.create_task(scheduler(app))
    await app.run_polling()

# 👇 اصلاح شده برای Render و Python 3.13 👇
if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
