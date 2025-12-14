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
async def start_handler(message: Message, state: FSMContext):
    await message.answer(
        "👋 Добро пожаловать!\n\nНажмите '📊 Заполнить отчёт' для начала.",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "📊 Заполнить отчёт")
async def start_report(message: Message, state: FSMContext):
    await message.answer("📋 Выберите сессию:", reply_markup=get_sessions_keyboard())
    await state.set_state(ReportStates.waiting_session)

@dp.message(ReportStates.waiting_session)
async def session_chosen(message: Message, state: FSMContext):
    if message.text == "⬅️ Отмена":
        await state.clear()
        await message.answer("❌ Отмена.", reply_markup=get_main_keyboard())
        return
    await state.update_data(session=message.text)
    await message.answer("🕐 Выберите смену:", reply_markup=get_shifts_keyboard())
    await state.set_state(ReportStates.waiting_shift)

@dp.message(ReportStates.waiting_shift)
async def shift_chosen(message: Message, state: FSMContext):
    if message.text == "⬅️ Отмена":
        await state.clear()
        await message.answer("❌ Отмена.", reply_markup=get_main_keyboard())
        return
    await state.update_data(shift=message.text)
    today = get_today_date()
    await state.update_data(date=today, user=message.from_user.first_name)
    await message.answer(f"💰 Баланс за смену {message.text}\n(вписывайте С ВЫЧЕТОМ комиссий платформы):")
    await state.set_state(ReportStates.waiting_balance)

@dp.message(ReportStates.waiting_balance)
async def balance_chosen(message: Message, state: FSMContext):
    await state.update_data(balance=message.text)
    await message.answer("✅ Выполнение чек-листа? (Да/Нет/Частично):")
    await state.set_state(ReportStates.waiting_checklist)

@dp.message(ReportStates.waiting_checklist)
async def checklist_chosen(message: Message, state: FSMContext):
    await state.update_data(checklist=message.t
