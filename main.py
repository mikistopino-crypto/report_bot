import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

load_dotenv()
logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(storage=MemoryStorage())

class ReportStates(StatesGroup):
    waiting_session = State()
    waiting_shift = State()
    waiting_balance = State()
    waiting_checklist = State()
    waiting_shift_description = State()
    waiting_fans = State()
    waiting_tops = State()

def get_today_date():
    return datetime.now().strftime("%d.%m.%Y")

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Заполнить отчёт")],
            [KeyboardButton(text="ℹ️ Инструкция")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_sessions_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Алина 1 OnlyFans"), KeyboardButton(text="Алина 1 Fansly")],
            [KeyboardButton(text="Алина 2 OnlyFans"), KeyboardButton(text="Алина 2 Fansly")],
            [KeyboardButton(text="⬅️ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_shifts_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="00:00 - 06:00"), KeyboardButton(text="06:00 - 12:00")],
            [KeyboardButton(text="12:00 - 18:00"), KeyboardButton(text="18:00 - 00:00")],
            [KeyboardButton(text="⬅️ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

@dp.message(F.text == "/start")
async def start_handler
import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

load_dotenv()
logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(storage=MemoryStorage())

class ReportStates(StatesGroup):
    waiting_session = State()
    waiting_shift = State()
    waiting_balance = State()
    waiting_checklist = State()
    waiting_shift_description = State()
    waiting_fans = State()
    waiting_tops = State()

def get_today_date():
    return datetime.now().strftime("%d.%m.%Y")

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Заполнить отчёт")],
            [KeyboardButton(text="ℹ️ Инструкция")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_sessions_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Алина 1 OnlyFans"), KeyboardButton(text="Алина 1 Fansly")],
            [KeyboardButton(text="Алина 2 OnlyFans"), KeyboardButton(text="Алина 2 Fansly")],
            [KeyboardButton(text="⬅️ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_shifts_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="00:00 - 06:00"), KeyboardButton(text="06:00 - 12:00")],
            [KeyboardButton(text="12:00 - 18:00"), KeyboardButton(text="18:00 - 00:00")],
            [KeyboardButton(text="⬅️ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

@dp.message(F.text == "/start")
async def start_handler
