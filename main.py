import os
import asyncio
import logging
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
    waiting_shift_time = State()
    waiting_balance = State()
    waiting_checklist = State()
    waiting_comment = State()
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

# Сессия
@dp.message(ReportStates.waiting_session)
async def session_chosen(message: Message, state: FSMContext):
    if message.text == "⬅️ Отмена":
        await state.clear()
        await message.answer("❌ Отмена.", reply_markup=get_main_keyboard())
        return
    
    await state.update_data(session=message.text)
    await message.answer("⏰ Время смены (например: 14:00-22:00):")
    await state.set_state(ReportStates.waiting_shift_time)

# Время смены
@dp.message(ReportStates.waiting_shift_time)
async def shift_time_chosen(message: Message, state: FSMContext):
    await state.update_data(shift_time=message.text)
    await message.answer("💰 Баланс/выручка:")
    await state.set_state(ReportStates.waiting_balance)

# Баланс
@dp.message(ReportStates.waiting_balance)
async def balance_chosen(message: Message, state: FSMContext):
    await state.update_data(balance=message.text)
    await message.answer("✅ Чек-лист? (Да/Нет/Частично):")
    await state.set_state(ReportStates.waiting_checklist)

# Чек-лист
@dp.message(ReportStates.waiting_checklist)
async def checklist_chosen(message: Message, state: FSMContext):
    await state.update_data(checklist=message.text)
    await message.answer("💬 Комментарий:")
    await state.set_state(ReportStates.waiting_comment)

# Комментарий
@dp.message(ReportStates.waiting_comment)
async def comment_chosen(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await message.answer("👥 Фаны:")
    await state.set_state(ReportStates.waiting_fans)

# Фаны
@dp.message(ReportStates.waiting_fans)
async def fans_chosen(message: Message, state: FSMContext):
    await state.update_data(fans=message.text)
    await message.answer("🏆 Топы:")
    await state.set_state(ReportStates.waiting_tops)

# Финал отчёта
@dp.message(ReportStates.waiting_tops)
async def finalize_report(message: Message, state: FSMContext):
    data = await state.get_data()
    
    report_text = f"""📊 ОТЧЁТ

📋 Сессия: {data['session']}
⏰ Смена: {data['shift_time']}
💰 Баланс: {data['balance']}
✅ Чек-лист: {data['checklist']}
💬 Комментарий: {data['comment']}
👥 Фаны: {data['fans']}
🏆 Топы: {message.text}"""

    # Отправка в группу
    group_id = os.getenv('GROUP_ID')
    thread_reports = os.getenv('THREAD_REPORTS')
    
    await bot.send_message(
        chat_id=group_id,
        message_thread_id=int(thread_reports),
        text=report_text
    )
    
    await message.answer("✅ Отчёт отправлен!", reply_markup=get_main_keyboard())
    await state.clear()

# Инструкция
@dp.message(F.text == "ℹ️ Инструкция")
async def show_help(message: Message):
    await message.answer(
        "📖 Заполните отчёт по шагам:\n"
        "1. Сессия → 2. Время → 3. Баланс → 4. Чек-лист → 5. Комментарий → 6. Фаны → 7. Топы",
        reply_markup=get_main_keyboard()
    )

# Запуск
async def start_bot():
    print("🚀 Starting bot...")
    await dp.start_polling(bot)

async def main():
    await asyncio.gather(start_bot(), fake_web_server())

if __name__ == '__main__':
    print("🎯 Report bot + Render fake server")
    asyncio.run(main())
