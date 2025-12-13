import asyncio
import aiosqlite
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import BOT_TOKEN, GROUP_ID, THREAD_REPORTS, THREAD_TOPS
from datetime import datetime

logging.basicConfig(level=logging.INFO)
dp = Dispatcher(storage=MemoryStorage())
bot = Bot(token=BOT_TOKEN)

class ReportForm(StatesGroup):
    waiting_session = State()
    waiting_shift = State()
    waiting_balance = State()
    waiting_checklist = State()
    waiting_comment = State()
    waiting_fans = State()
    waiting_tops = State()

# Инициализация БД
async def init_db():
    async with aiosqlite.connect('bot.db') as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, role TEXT)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY, name TEXT, role TEXT, date TEXT)''')
        
        # Тестовые данные для 13.12
        test_sessions = [
            ("алина 1 Onlyfans", "operator_of", "13.12"),
            ("алина 1 fansly", "operator_fl", "13.12")
        ]
        for name, role, date in test_sessions:
            await db.execute("INSERT OR IGNORE INTO sessions (name, role, date) VALUES (?, ?, ?)", 
                           (name, role, date))
        await db.commit()

# Роли пользователей
async def get_user_role(user_id: int) -> str:
    async with aiosqlite.connect('bot.db') as db:
        cursor = await db.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()
        if result:
            return result[0]
        # По умолчанию оператор OF
        await db.execute("INSERT OR IGNORE INTO users (user_id, role) VALUES (?, 'operator_of')", (user_id,))
        await db.commit()
        return 'operator_of'

async def get_sessions(role: str, date: str) -> list:
    async with aiosqlite.connect('bot.db') as db:
        cursor = await db.execute("SELECT name FROM sessions WHERE role = ? AND date = ?", (role, date))
        return [row[0] for row in await cursor.fetchall()]

def sessions_keyboard(sessions: list):
    builder = InlineKeyboardBuilder()
    for session in sessions:
        builder.button(text=session, callback_data=f"session:{session}")
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()

def shifts_keyboard():
    builder = InlineKeyboardBuilder()
    shifts = ["16:00-00:00", "00:00-06:00", "06:00-12:00", "12:00-18:00"]
    for shift in shifts:
        builder.button(text=shift, callback_data=f"shift:{shift}")
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()

@dp.message(Command("start"))
async def start_handler(message: Message, state):
    today = datetime.now().strftime("%d.%m")
    role = await get_user_role(message.from_user.id)
    sessions = await get_sessions(role, today)
    
    if not sessions:
        await message.answer("❌ Нет доступных сессий для вашей роли")
        return
    
    await message.answer(
        f"👋 {message.from_user.full_name}\n🎭 Роль: {role}\n\nВыберите сессию:",
        reply_markup=sessions_keyboard(sessions)
    )
    await state.set_state(ReportForm.waiting_session)

# Обработчики шагов формы (упрощенные)
@dp.callback_query(F.data.startswith("session:"), ReportForm.waiting_session)
async def select_session(callback: CallbackQuery, state):
    session = callback.data.split(":", 1)[1]
    await state.update_data(session=session)
    await callback.message.edit_text(
        f"✅ Сессия: {session}\n\n⏰ Выберите смену:",
        reply_markup=shifts_keyboard()
    )
    await state.set_state(ReportForm.waiting_shift)
    await callback.answer()

@dp.callback_query(F.data.startswith("shift:"), ReportForm.waiting_shift)
async def select_shift(callback: CallbackQuery, state):
    shift = callback.data.split(":", 1)[1]
    await state.update_data(shift=shift)
    data = await state.get_data()
    
    await callback.message.edit_text(
        f"📊 Сессия: {data['session']}\n⏰ Смена: {shift}\n\n💰 Введите <b>баланс смены</b>:",
        parse_mode="HTML"
    )
    await state.set_state(ReportForm.waiting_balance)
    await callback.answer()

@dp.message(ReportForm.waiting_balance)
async def balance_handler(message: Message, state):
    await state.update_data(balance=message.text)
    await message.answer("📋 Выполнение чек-листа (да/нет/частично):")
    await state.set_state(ReportForm.waiting_checklist)

@dp.message(ReportForm.waiting_checklist)
async def checklist_handler(message: Message, state):
    await state.update_data(checklist=message.text)
    await message.answer("💬 Введите комментарий по смене:")
    await state.set_state(ReportForm.waiting_comment)

@dp.message(ReportForm.waiting_comment)
async def comment_handler(message: Message, state):
    await state.update_data(comment=message.text)
    await message.answer("👥 Информация по фанам:")
    await state.set_state(ReportForm.waiting_fans)

@dp.message(ReportForm.waiting_fans)
async def fans_handler(message: Message, state):
    await state.update_data(fans=message.text)
    await message.answer("🏆 Информация по топам:")
    await state.set_state(ReportForm.waiting_tops)

@dp.message(ReportForm.waiting_tops)
async def complete_report(message: Message, state):
    data = await state.get_data()
    data['tops'] = message.text
    data['user'] = message.from_user.full_name
    data['time'] = datetime.now().strftime('%H:%M %d.%m')
    
    # 📤 ОТЧЕТ БЕЗ ТОПОВ
    report_text = f"""📊 <b>ОТЧЕТ СМЕНЫ</b>
👤 {data['user']}
📅 {data['session']} | {data['shift']}
💰 <b>Баланс: {data['balance']}</b>
📋 Чек-лист: {data['checklist']}
💬 {data['comment']}
👥 Фаны: {data['fans']}

⏰ {data['time']}"""
    
    # 📤 ТОПЫ ОТДЕЛЬНО
    tops_text = f"""🏆 <b>ТОПЫ</b>
📅 {data['session']} | {data['shift']}
{data['tops']}

👤 {data['user']} | {data['time']}"""
    
    # ✅ ОТПРАВЛЯЕМ В ГРУППУ
    await bot.send_message(
        GROUP_ID, report_text, 
        message_thread_id=THREAD_REPORTS,
        parse_mode="HTML"
    )
    await bot.send_message(
        GROUP_ID, tops_text, 
        message_thread_id=THREAD_TOPS,
        parse_mode="HTML"
    )
    
    await message.answer("✅ <b>Отчет успешно отправлен!</b>\n\nНачните новый: /start", parse_mode="HTML")
    await state.clear()

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
