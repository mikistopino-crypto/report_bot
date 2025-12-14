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
    waiting_shift = State()
    waiting_balance = State()
    waiting_checklist = State()
    waiting_shift_description = State()
    waiting_fans = State()
    waiting_tops = State()

# Фейковый HTTP сервер для Render
async def fake_web_server():
    app = web.Application()
    app.router.add_get('/', lambda _: web.Response(text='OK'))
    app.router.add_get('/health', lambda _: web.Response(text='healthy'))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    print("✅ Fake HTTP server на порту 10000")
    await asyncio.Event().wait()

# Получить текущую дату
def get_today_date():
    return datetime.now().strftime("%d.%m.%Y")

# Главное меню
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Заполнить отчёт")],
            [KeyboardButton(text="ℹ️ Инструкция")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

# Клавиатура сессий
def get_sessions_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Алина 1 OnlyFans"), KeyboardButton(text="Алина 1 Fansly")],
            [KeyboardButton(text="Алина 2 OnlyFans"), KeyboardButton(text="Алина 2 Fansly")],
            [KeyboardButton(text="⬅️ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

# Клавиатура смен
def get_shifts_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="00:00 - 06:00"), KeyboardButton(text="06:00 - 12:00")],
            [KeyboardButton(text="12:00 - 18:00"), KeyboardButton(text="18:00 - 00:00")],
            [KeyboardButton(text="⬅️ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

# Старт
@dp.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "Нажмите '📊 Заполнить отчёт' для начала.",
        reply_markup=get_main_keyboard()
    )

# Начало отчёта
@dp.message(F.text == "📊 Заполнить отчёт")
async def start_report(message: Message, state: FSMContext):
    await message.answer(
        "📋 Выберите сессию:",
        reply_markup=get_sessions_keyboard()
    )
    await state.set_state(ReportStates.waiting_session)

# Сессия выбрана
@dp.message(ReportStates.waiting_session)
async def session_chosen(message: Message, state: FSMContext):
    if message.text == "⬅️ Отмена":
        await state.clear()
        await message.answer("❌ Отмена.", reply_markup=get_main_keyboard())
        return
    
    await state.update_data(session=message.text)
    await message.answer(
        "🕐 Выберите смену:",
        reply_markup=get_shifts_keyboard()
    )
    await state.set_state(ReportStates.waiting_shift)

# Смена выбрана
@dp.message(ReportStates.waiting_shift)
async def shift_chosen(message: Message, state: FSMContext):
    if message.text == "⬅️ Отмена":
        await state.clear()
        await message.answer("❌ Отмена.", reply_markup=get_main_keyboard())
        return
    
    await state.update_data(shift=message.text)
    today = get_today_date()
    await state.update_data(date=today, user=message.from_user.first_name)
    
    await message.answer(
        f"💰 Баланс за смену {message.text}\n"
        f"(вписывайте С ВЫЧЕТОМ комиссий платформы):"
    )
    await state.set_state(ReportStates.waiting_balance)

# Баланс
@dp.message(ReportStates.waiting_balance)
async def balance_chosen(message: Message, state: FSMContext):
    await state.update_data(balance=message.text)
    await message.answer("✅ Выполнение чек-листа? (Да/Нет/Частично):")
    await state.set_state(ReportStates.waiting_checklist)

# Чек-лист
@dp.message(ReportStates.waiting_checklist)
async def checklist_chosen(message: Message, state: FSMContext):
    await state.update_data(checklist=message.text)
    
    # ОСНОВНОЙ ОТЧЁТ (без топов)
    data = await state.get_data()
    main_report = f"""📊 СМЕННЫЙ ОТЧЁТ

📅 {data['date']} / {data['shift']} / {data['user']}
💰 Баланс: ${data['balance']} (с вычетом комиссий)
✅ Чек-лист: {data['checklist']}

⏳ Ожидаем описание смены..."""
    
    # Отправляем основной отчёт в ветку REPORTS
    group_id = os.getenv('GROUP_ID')
    thread_reports = os.getenv('THREAD_REPORTS')
    
    await bot.send_message(
        chat_id=group_id,
        message_thread_id=int(thread_reports),
        text=main_report
    )
    
    await message.answer(
        "📝 Что сделали на смене для получения этого баланса?\n"
        "Что не получилось для заработка больше?\n\n"
        "(пишите подробно)"
    )
    await state.set_state(ReportStates.waiting_shift_description)

# Описание смены
@dp.message(ReportStates.waiting_shift_description)
async def shift_description_chosen(message: Message, state: FSMContext):
    await state.update_data(shift_description=message.text)
    await message.answer("👥 Отчёт по фанам:\n\nПример: `T*p*un @jw*s1*41 скупает все анал видео по 40 баксов. меньше не продавайте ему, слишком спекулятивный`")
    await state.set_state(ReportStates.waiting_fans)

# Фаны
@dp.message(ReportStates.waiting_fans)
async def fans_chosen(message: Message, state: FSMContext):
    await state.update_data(fans=message.text)
    await message.answer("🏆 Отчёт по топам:\n\nПример: `M*rc C*lm*r @u44*72*2*5 типнул просто так, продолжаем игнорить! нужно выжимать на кастом через обиду`")
    await state.set_state(ReportStates.waiting_tops)

# ТОПЫ - ОТДЕЛЬНО!
@dp.message(ReportStates.waiting_tops)
async def tops_chosen(message: Message, state: FSMContext):
    data = await state.get_data()
    
    # ФИНАЛЬНЫЙ ОСНОВНОЙ ОТЧЁТ (дополняем описание)
    final_main_report = f"""📊 СМЕННЫЙ ОТЧЁТ

📅 {data['date']} / {data['shift']} / {data['user']}
💰 Баланс: ${data['balance']} (с вычетом комиссий)
✅ Чек-лист: {data['checklist']}
📝 Смена: {data['shift_description']}
👥 Фаны: {data['fans']}"""
    
    # Обновляем основной отчёт
    group_id = os.getenv('GROUP_ID')
    thread_reports = os.getenv('THREAD_REPORTS')
    
    await bot.edit_message_text(
        text=final_main_report,
        chat_id=group_id,
        message_thread_id=int(thread_reports),
        message_id=await get_last_message_id(group_id, thread_reports)  # упрощенно
    )
    
    # ОТДЕЛЬНЫЙ ОТЧЁТ ПО ТОПАМ
    tops_report = f"""🏆 ТОПЫ ДНЯ

📅 {data['date']} {data['shift']}
👤 Сменщик: {data['user']}
📝 {message.text}"""
    
    thread_tops = os.getenv('THREAD_TOPS')
    await bot.send_message(
        chat_id=group_id,
        message_thread_id=int(thread_tops),
        text=tops_report
    )
    
    await message.answer(
        "✅ Отчёт полностью отправлен!\n\n"
        "• Основной отчёт в 📊 REPORTS\n"
        "• Топы в 🏆 TOPS",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

# Инструкция
@dp.message(F.text == "ℹ️ Инструкция")
async def show_help(message: Message):
    await message.answer(
        "📖 Пошагово:\n"
        "1️⃣ Сессия → 2️⃣ Смена (4 варианта)\n"
        "3️⃣ Баланс (минус комиссии)\n"
        "4️⃣ Чек-лист → 5️⃣ Описание смены\n"
        "6️⃣ Фаны → 7️⃣ Топы\n\n"
        "✅ Основной отчёт → THREAD_REPORTS\n"
        "⭐ Топы отдельно → THREAD_TOPS",
        reply_markup=get_main_keyboard()
    )

# Запуск
async def start_bot():
    print("🚀 Starting bot...")
    await dp.start_polling(bot)

async def main():
    await asyncio.gather(start_bot(), fake_web_server())

if __name__ == '__main__':
    print("🎯 Report bot v2.0 + Render fake server")
    asyncio.run(main())
