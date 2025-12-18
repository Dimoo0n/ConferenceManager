import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import sqlite3
from validators import validate_group_name, validate_conf_date, validate_url

API_TOKEN = '8593640683:AAFYUu1sIgebbneJfSf9cbCbejDUoWSvNv8'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()


class ConferenceSG(StatesGroup):
    waiting_for_name = State()
    waiting_for_date = State()
    waiting_for_link = State()


def get_user_role(tg_id):
    conn = sqlite3.connect('conference_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE tg_id = ?", (tg_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 'guest'


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    role = get_user_role(message.from_user.id)
    await message.answer(f"Вітаю! Ваша роль: {role}.")


@dp.message(Command("create_group"))
async def create_group(message: types.Message):
    role = get_user_role(message.from_user.id)
    if role not in ['teacher', 'admin']:
        await message.answer("Помилка: Недостатньо прав! ")
        return

    group_name = message.text.replace('/create_group ', '').strip()

    if not validate_group_name(group_name):
        await message.answer("Помилка: Назва має бути від 2 до 20 символів.")
        return

    conn = sqlite3.connect('conference_bot.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO groups (name) VALUES (?)", (group_name,))
        conn.commit()
        await message.answer(f"Групу '{group_name}' успішно створено! ")
    except sqlite3.IntegrityError:
        await message.answer("Помилка: Група з такою назвою вже існує.")
    finally:
        conn.close()


@dp.message(Command("create_conference"))
async def start_conf_creation(message: types.Message, state: FSMContext):
    role = get_user_role(message.from_user.id)
    if role not in ['teacher', 'admin']:
        await message.answer("Доступ обмежено.")
        return

    await message.answer("Введіть назву конференції (3-100 символів): ")
    await state.set_state(ConferenceSG.waiting_for_name)


@dp.message(ConferenceSG.waiting_for_name)
async def process_conf_name(message: types.Message, state: FSMContext):
    if 3 <= len(message.text) <= 100:
        await state.update_data(topic=message.text)
        await message.answer("Введіть дату та час (DD.MM.YYYY HH:MM): ")
        await state.set_state(ConferenceSG.waiting_for_date)
    else:
        await message.answer("Некоректна довжина назви. Спробуйте ще раз. ")


@dp.message(ConferenceSG.waiting_for_date)
async def process_conf_date(message: types.Message, state: FSMContext):
    try:
        date_part = message.text.split()[0]
        if not validate_conf_date(date_part):
            await message.answer("Помилка: дата у минулому або неправильний формат.")
            return

        await state.update_data(date=message.text.split()[0], time=message.text.split()[1])
        await message.answer("Введіть посилання на Zoom/Meet: ")
        await state.set_state(ConferenceSG.waiting_for_link)
    except ValueError:
        await message.answer("Невірний формат! Очікується: DD.MM.YYYY HH:MM ")


@dp.message(ConferenceSG.waiting_for_link)
async def process_conf_link(message: types.Message, state: FSMContext):
    if not validate_url(message.text):
        await message.answer("Помилка: Посилання має починатися з http/https.")
        return

    data = await state.get_data()
    conn = sqlite3.connect('conference_bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conferences (topic, conf_date, conf_time, link, group_id) VALUES (?, ?, ?, ?, ?)",
                   (data['topic'], data['date'], data['time'], message.text, 1))
    conn.commit()
    conn.close()

    await message.answer("Конференцію успішно створено! Учасники отримають сповіщення. ")
    await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())