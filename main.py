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
    await state.update_data(checklist=message.text)
    await message.answer("📝 Что сделали на смене для получения этого баланса?\nЧто не получилось для заработка больше?\n(пишите подробно)")
    await state.set_state(ReportStates.waiting_shift_description)

@dp.message(ReportStates.waiting_shift_description)
async def shift_description_chosen(message: Message, state: FSMContext):
    await state.update_data(shift_description=message.text)
    await message.answer("👥 Отчёт по фанам:\nПример: `T*p*un @jw*s1*41 скупает все анал видео по 40 баксов`")
    await state.set_state(ReportStates.waiting_fans)

@dp.message(ReportStates.waiting_fans)
async def fans_chosen(message: Message, state: FSMContext):
    await state.update_data(fans=message.text)
    await message.answer("🏆 Отчёт по топам:\nПример: `M*rc C*lm*r @u44*72*2*5 типнул просто так`")
    await state.set_state(ReportStates.waiting_tops)

@dp.message(ReportStates.waiting_tops)
async def finalize_report(message: Message, state: FSMContext):
    data = await state.get_data()
    
    main_report = f"""📊 ОТЧЕТ ПО СМЕНЕ (СЕССИЯ/ЮЗЕР СМЕНЩИКА)

📅 {data['date']} / {data['shift']} / {data['user']}
💰 Баланс: ${data['balance']} (с вычетом комиссий)
✅ Чек-лист: {data['checklist']}
📝 Смена: {data['shift_description']}
👥 Фаны: {data['fans']}"""
    
    tops_report = f"""ОТЧЕТЫ ПО ТОПАМ

📅 {data['date']} {data['shift']}
👤 Юзер сменщика: {data['user']}
📝 {message.text}"""
    
    group_id = os.getenv('GROUP_ID')
    thread_reports = os.getenv('THREAD_REPORTS')
    thread_tops = os.getenv('THREAD_TOPS')
    
    await bot.send_message(chat_id=group_id, message_thread_id=int(thread_reports), text=main_report)
    await bot.send_message(chat_id=group_id, message_thread_id=int(thread_tops), text=tops_report)
    
    await message.answer("✅ Отчёт полностью отправлен!\n📊 Основной → REPORTS\n🏆 Топы → TOPS", reply_markup=get_main_keyboard())
    await state.clear()

@dp.message(F.text == "ℹ️ Инструкция")
async def show_help(message: Message):
    await message.answer(
        "📖 Пошагово:\n1️⃣ Сессия → 2️⃣ Смена → 3️⃣ Баланс → 4️⃣ Чек-лист\n5️⃣ Описание → 6️⃣ Фаны → 7️⃣ Топы\n✅ Отчёты только после топов!",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "⬅️ Отмена")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отмена.", reply_markup=get_main_keyboard())

async def fake_web_server():
    app = web.Application()
    app.router.add_get('/', lambda _: web.Response(text='Report Bot OK'))
    app.router.add_get('/health', lambda _: web.Response(text='healthy'))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    print("✅ Fake HTTP server на порту 10000 ✓ Render happy!")
    await asyncio.Event().wait()

async def bot_polling():
    print("🚀 Starting bot polling...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook cleared")
    except:
        print("ℹ️ No webhook")
    await dp.start_polling(bot)

async def main():
    print("🎯 Report Bot v12.0 — ФИНАЛЬНАЯ ВЕРСИЯ!")
    await asyncio.gather(fake_web_server(), bot_polling())

if __name__ == '__main__':
    asyncio.run(main())
