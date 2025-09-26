import asyncio, random, logging
from datetime import datetime, timedelta
import pytz
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

TOKEN = "8471259728:AAENcc8jzuCepgfOWuFZd3FjAo0tRsjiWhE"
TZ = pytz.timezone("Asia/Yekaterinburg")

logging.basicConfig(level=logging.INFO)
bot = Bot(TOKEN)
dp = Dispatcher()

# Сообщения
DAILY = [
    "Иля, пора пить таблетки 💊",
    "Не забудь про таблетки, Иля 🌸",
    "Таблеточки ждут тебя, Иля 😘",
    "Время лечиться! Иля, не забывай 💖",
]
REPEAT = ["Пей давай 💊", "Не тяни, Иля!", "Давай-давай 💖"]

# Кнопки
keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Я выпила"), KeyboardButton(text="Не выпила ещё")]],
    resize_keyboard=True
)

# Подписчики: chat_id -> { days_left, last_taken, spam_task }
subscribers = {}
REMINDER_DAYS = 14
REMINDER_HOUR = 18
INTERVAL_MIN = 10
DURATION_HOURS = 1

@dp.message(Command("start"))
async def cmd_start(message: Message):
    cid = message.chat.id
    if cid not in subscribers:
        subscribers[cid] = {"days_left": REMINDER_DAYS, "last_taken": None, "spam_task": None}
    await message.answer("Привет, Иля! Я буду напоминать тебе про таблетки 💊 (18:00 по Челябинску).", reply_markup=keyboard)

@dp.message(F.text == "Я выпила")
async def did_take(message: Message):
    cid = message.chat.id
    data = subscribers.get(cid)
    today = datetime.now(TZ).date()
    if data:
        data["last_taken"] = today
        task = data.get("spam_task")
        if task and not task.done():
            task.cancel()
        data["spam_task"] = None
    await message.answer("Умничка моя 💖")

@dp.message(F.text == "Не выпила ещё")
async def not_yet(message: Message):
    await message.answer("Пей давай 💊")

async def spam_reminders(cid: int):
    try:
        start = datetime.now(TZ)
        end = start + timedelta(hours=DURATION_HOURS)
        while datetime.now(TZ) < end:
            await asyncio.sleep(INTERVAL_MIN * 60)
            data = subscribers.get(cid)
            if not data:
                return
            if data.get("last_taken") == datetime.now(TZ).date():
                return
            await bot.send_message(cid, random.choice(REPEAT), reply_markup=keyboard)
    except asyncio.CancelledError:
        return
    finally:
        if cid in subscribers:
            subscribers[cid]["spam_task"] = None

async def daily_loop():
    while True:
        now = datetime.now(TZ)
        target = now.replace(hour=REMINDER_HOUR, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())
        for cid, data in list(subscribers.items()):
            if data["days_left"] <= 0:
                subscribers.pop(cid, None)
                continue
            if data.get("last_taken") == datetime.now(TZ).date():
                continue
            await bot.send_message(cid, random.choice(DAILY), reply_markup=keyboard)
            data["days_left"] -= 1
            if data.get("spam_task") is None:
                task = asyncio.create_task(spam_reminders(cid))
                data["spam_task"] = task

async def main():
    asyncio.create_task(daily_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
