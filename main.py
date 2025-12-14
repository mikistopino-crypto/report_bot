import os
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import uvicorn
from aiohttp import web

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(storage=MemoryStorage())

# Состояния FSM
class ReportStates(StatesGroup):
    waiting_session = State()
    waiting_shift_time = State()
    waiting_balance = State()
    waiting_checklist = State()
    waiting_comment = State()
    waiting_fans = State()
    waiting_tops = State()

# Фейковый HTTP сервер для Render (ВАЖНО!)
async def fake_web_server():
    """Фейковый сервер для Render на порту 10000"""
    app = web.Application()
    app.router.add_get('/', lambda _: web.Response(text='OK'))
    app.router.add_get('/health', lambda _: web.Response(text='healthy'))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    print("✅ Fake HTTP server на порту 10000 (Render happy)")
    await asyncio.Event().wait()  # держим сервер вечно

# Главное меню
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Заполнить отчёт")],
            [KeyboardButton(text="ℹ️ Инструкция")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Клавиатура сессий (пример)
def get_sessions_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Алина 1 OnlyFans"), KeyboardButton(text="Алина 1 Fansly")],
            [KeyboardButton(text="Алина 2 OnlyFans"), KeyboardButton(text="Алина 2 Fansly")],
            [KeyboardButton(text="⬅️ Отмена")]
        ],
        resize_keyboard=
