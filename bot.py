import os
import json
from datetime import date, datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import asyncio
from dotenv import load_dotenv

# Загружаем токен из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "users.json"

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env файле!")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# --- Функции работы с данными ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_id):
    data = load_data()
    str_id = str(user_id)
    if str_id not in data:
        data[str_id] = {"last_reset": None, "chat_id": user_id}
        save_data(data)
    return data[str_id]

def reset_streak(user_id):
    data = load_data()
    str_id = str(user_id)
    data[str_id]["last_reset"] = str(date.today())
    save_data(data)

def get_streak(user_id):
    user = get_user(user_id)
    if user["last_reset"] is None:
        return 0
    last_reset = datetime.strptime(user["last_reset"], "%Y-%m-%d").date()
    return (date.today() - last_reset).days

# --- Обработчики сообщений ---
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🆘 У меня триггер!")],
        [KeyboardButton(text="🔄 Я сорвался")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def send_welcome(message: Message):
    get_user(message.from_user.id)  # гарантируем создание профиля
    await message.answer(
        "🧠 <b>Привет, воин!</b>\n\n"
        "Я помогу тебе пройти путь NoFap.\n\n"
        "• Нажми <b>🆘</b>, когда почувствуешь слабость\n"
        "• Нажми <b>🔄</b>, если был срыв (обнуляет счётчик)\n"
        "• Пиши <b>/status</b>, чтобы увидеть свой прогресс\n\n"
        "Каждые 3 часа я буду присылать тебе мотивацию.",
        reply_markup=keyboard
    )

@dp.message(lambda msg: msg.text == "🆘 У меня триггер!")
async def handle_trigger(message: Message):
    streak = get_streak(message.from_user.id)
    await message.answer(
        f"🔥 <b>Ты на {streak}-м дне!</b>\n\n"
        "Это желание — просто волна. Она придёт и уйдёт.\n"
        "Подумай о том, кем ты станешь через месяц такой силы.\n\n"
        "<i>Ты уже победил тысячи раз. Сделай это снова.</i>"
    )

@dp.message(lambda msg: msg.text == "🔄 Я сорвался")
async def handle_reset(message: Message):
    reset_streak(message.from_user.id)
    await message.answer(
        "💔 <b>Срыв — не конец пути.</b>\n\n"
        "Это часть роста. Главное — встать и идти дальше.\n"
        "Счётчик обнулён. Новый старт — прямо сейчас.\n\n"
        "Я верю в тебя. В следующий раз ты продержишься дольше."
    )

@dp.message(Command("status"))
async def show_status(message: Message):
    streak = get_streak(message.from_user.id)
    if streak == 0:
        await message.answer(
            "🕗 Ты ещё не начал отсчёт.\n"
            "Нажми <b>🔄 Я сорвался</b>, чтобы начать с сегодняшнего дня."
        )
    else:
        await message.answer(f"✅ <b>Твой текущий стрик: {streak} дней.</b>")

# --- Функция отправки напоминаний ---
async def send_reminder():
    data = load_data()
    for user_id_str, user_data in data.items():
        try:
            streak = get_streak(int(user_id_str))
            await bot.send_message(
                chat_id=user_data["chat_id"],
                text=(
                    f"⏰ <b>Напоминание ({datetime.now().strftime('%H:%M')})</b>\n\n"
                    f"Ты на <b>{streak}</b>-м дне пути NoFap.\n"
                    "Каждая минута без уступки — это победа над старой версией себя.\n\n"
                    "Не сдавайся. Ты сильнее, чем думаешь. 💪"
                )
            )
        except Exception as e:
            print(f"Не удалось отправить напоминание пользователю {user_id_str}: {e}")

# --- Запуск ---
async def main():
    # Добавляем задачу: каждые 3 часа
    scheduler.add_job(send_reminder, "interval", hours=3, id="nofap_reminder")
    scheduler.start()

    print("✅ Бот запущен! Напоминания каждые 3 часа.")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())