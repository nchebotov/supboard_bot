import asyncio
import time
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
)

from config import BOT_TOKEN, ADMINS, SAPBOARDS, RENTAL_RATE
import database
import gsheet
import logging
import pytz



bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)


def get_saratov_time():
    return datetime.now(tz=pytz.timezone("Europe/Saratov"))

# FSM состояния
class RentStates(StatesGroup):
    choosing_sapboard = State()
    entering_hours = State()
    confirming = State()
    waiting_for_sapboard_id = State()


# Хранение активных аренд
active_rentals = {}  # {sapboard_id: {"sapboard_id": ..., "sapboard_name": ..., "admin_id": ..., "admin_name": ..., "end_time": ..., "task": ...}}


# Главная клавиатура
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Аренда доски")],
        [KeyboardButton(text="Принудительно завершить аренду доски")],
        [KeyboardButton(text="Статус")],
        [KeyboardButton(text="Помощь")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    input_field_placeholder="Выберите действие"
)


def is_admin(user_id):
    return user_id in ADMINS


def format_time(t):
    return t.strftime("%Y-%m-%d %H:%M")


@dp.startup()
async def on_startup():
    gsheet.init_sheet()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    if is_admin(message.from_user.id):
        await message.answer(
            f"Привет, {message.from_user.username}!\n Используйте /help чтобы посмотреть список команд.",
            reply_markup=main_keyboard
        )
    else:
        await message.answer(" Вы не являетесь администратором.")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    if not is_admin(message.from_user.id):
        return

    help_text = (
        f"📌 *Доступные команды для администратора:*\n\n"
        "/start — Приветственное сообщение\n"
        "/help — Показать это меню\n"
        "/rent — Начать новую аренду (выбор доски, времени)\n"
        "/status — Посмотреть текущие активные аренды\n"
        f"/end <ID клиента> — Завершить аренду вручную. Список id=[{list(SAPBOARDS.keys())}]\n"
        "/export — Получить ссылку на Google Таблицу со статистикой\n"
        "/history — вся история\n"
        "/history sapboard=1 — только по сапборду 1\n"
        "/history admin=123456789 — только от админа с ID 123456789\n"
    )

    await message.answer(help_text, parse_mode="Markdown")


@dp.message(Command("rent"))
async def cmd_rent(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=sid)]
            for sid, name in SAPBOARDS.items()
        ]
    )
    await message.answer("Выберите сапборд:", reply_markup=keyboard)
    await state.set_state(RentStates.choosing_sapboard)


@dp.callback_query(StateFilter(RentStates.choosing_sapboard))
async def choose_hours(query: CallbackQuery, state: FSMContext):
    sapboard_id = query.data
    await state.update_data(sapboard_id=sapboard_id)
    await query.message.edit_text("Введите продолжительность аренды в часах, минимально 0.5 (30 минут):")
    await state.set_state(RentStates.entering_hours)


@dp.message(StateFilter(RentStates.entering_hours))
async def confirm_rental(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return

    try:
        hours = float(message.text)
    except ValueError:
        await message.answer("❌ Введите число, например: 0.5, 1.5, 2 и т.д")
        return

    if hours < 0.5:
        await message.answer("❌ Минимальное время аренды — 0.5 часа (30 минут). Попробуйте ещё раз:")
        return

    if 12 < hours:
        await message.answer("❌ Максимальное время аренды — 12 часов. Попробуйте ещё раз:")
        return

    data = await state.get_data()
    sapboard_id = data["sapboard_id"]
    cost = RENTAL_RATE * hours

    await state.update_data(hours=hours, cost=cost)
    await message.answer(
        f"Вы выбрали {SAPBOARDS[sapboard_id]} на {hours} ч.\n"
        f"Стоимость: {cost:.2f} руб.\n\nПодтвердите оплату:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")]
        ])
    )
    await state.set_state(RentStates.confirming)


@dp.callback_query(StateFilter(RentStates.confirming))
async def process_confirmation(query: CallbackQuery, state: FSMContext):
    if not is_admin(query.from_user.id):
        await query.message.answer("У вас нет прав администратора.")
        return

    if query.data == "confirm":
        data = await state.get_data()
        sapboard_id = data["sapboard_id"]
        hours = data["hours"]
        user_id = query.from_user.id
        admin_id = query.from_user.id
        admin_name = query.from_user.full_name

        start_time = get_saratov_time()
        end_time = start_time + timedelta(hours=hours)

        database.add_rental_start(
            user_id,
            sapboard_id,
            SAPBOARDS[sapboard_id],
            admin_id,
            admin_name,
            start_time,
            end_time,
            hours,
            data["cost"]
        )

        gsheet.add_rental_to_sheet(
            user_id,
            sapboard_id,
            SAPBOARDS[sapboard_id],
            admin_id,
            admin_name,
            start_time,
            end_time,
            hours,
            data["cost"]
        )

        active_rentals[sapboard_id] = {
            "user_id": user_id,
            "sapboard_id": sapboard_id,
            "sapboard_name": SAPBOARDS[sapboard_id],
            "admin_id": admin_id,
            "admin_name": admin_name,
            "end_time": end_time,
            "task": asyncio.create_task(
                send_reminder(admin_id, end_time, sapboard_id, admin_name, user_id)
            )
        }

        await query.message.edit_text(
            f"✅ Аренда {SAPBOARDS[sapboard_id]} началась!\n"
            f"Выдана админом: {admin_name} (ID: {admin_id})\n"
            f"Вернуть до: {format_time(end_time)}\n"
            f"Стоимость: {data['cost']:.2f} руб."
        )

    else:
        await query.message.edit_text("❌ Аренда отменена.")

    await state.clear()


async def send_reminder(admin_id, end_time, sapboard_id, admin_name, user_id):
    now = get_saratov_time()
    delta = (end_time - now).total_seconds()
    if delta > 300:
        await asyncio.sleep(delta - 300)
        if user_id in active_rentals:
            await bot.send_message(
                admin_id,
                f"⚠️ До конца аренды {SAPBOARDS[sapboard_id]} осталось 5 минут. "
                f"Пора забрать у клиента.\n"
                f"Выдано админом: {admin_name}"
            )
        await asyncio.sleep(300)

    if user_id in active_rentals:
        await bot.send_message(
            admin_id,
            f"🔚 Аренда {SAPBOARDS[sapboard_id]} завершена. Сапборд можно вернуть."
        )
        del active_rentals[user_id]


@dp.message(Command("status"))
async def cmd_status(message: Message):
    if not is_admin(message.from_user.id):
        return

    now = datetime.now()
    expired = []

    # Удаление просроченных аренд
    for user_id, info in list(active_rentals.items()):
        if info["end_time"] <= now:
            expired.append(user_id)
            del active_rentals[user_id]

    if not active_rentals:
        await message.answer("Нет активных аренд.")
        return

    text = "🕒 Активные аренды:\n"
    for user_id, info in active_rentals.items():
        text += (
            f"👤 Админ: {info['admin_name']}\n"
            f"👤 Админ ID: {info['admin_id']}\n"
            f"🛹 Сапборд: {info['sapboard_name']}\n"
            f"🧑‍💼 Сапборд ID: {info['sapboard_id']}\n"
            f"⏰ Вернуть до: {format_time(info['end_time'])}\n"
            "───────────────\n"
        )

    await message.answer(text)


@dp.message(F.text == "Принудительно завершить аренду доски")
async def ask_sapboard_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return

    await message.answer("Введите ID сапборда (например: 1, 2):")
    await state.set_state(RentStates.waiting_for_sapboard_id)


@dp.message(RentStates.waiting_for_sapboard_id)
async def handle_end_rent(message: Message, state: FSMContext):
    sapboard_id = message.text.strip()

    found = None
    target_key = None

    for user_id, info in active_rentals.items():
        if info["sapboard_id"] == sapboard_id:
            found = info
            target_key = user_id
            break

    if not found:
        await message.answer(f"❌ Активная аренда для сапборда `{sapboard_id}` не найдена.")
        await state.clear()
        return

    rental_info = active_rentals.pop(target_key)
    rental_info["task"].cancel()

    await message.answer(f"✅ Аренда {rental_info['sapboard_name']} принудительно завершена.")
    await state.clear()


@dp.message(Command("export"))
async def cmd_export(message: Message):
    if not is_admin(message.from_user.id):
        return

    url = gsheet.get_sheet_url()
    await message.answer(f"📊 Таблица статистики аренды: [открыть в Google Sheets]({url})", parse_mode="Markdown")


@dp.message(Command("history"))
async def cmd_history(message: Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split()
    filters = {"sapboard": None, "admin": None}

    for arg in args[1:]:
        if arg.startswith("sapboard="):
            filters["sapboard"] = arg.split("=")[1]
        elif arg.startswith("admin="):
            filters["admin"] = arg.split("=")[1]

    all_rentals = database.get_all_rentals()

    filtered = []
    for r in all_rentals:
        _, user_id, sapboard_id, sapboard_name, admin_id, admin_name, start, end, duration, cost = r

        match = True
        if filters["sapboard"] and sapboard_id != filters["sapboard"]:
            match = False
        if filters["admin"] and str(admin_id) != filters["admin"]:
            match = False

        if match:
            filtered.append({
                "user_id": user_id,
                "sapboard_id": sapboard_id,
                "sapboard_name": sapboard_name,
                "admin_id": admin_id,
                "admin_name": admin_name,
                "start": start,
                "end": end,
                "duration": duration,
                "cost": cost
            })

    if not filtered:
        await message.answer("Нет записей по вашему запросу.")
        return

    text = "📜 История аренд:\n\n"
    for entry in filtered[:10]:  # показываем первые 10 записей
        text += (
            f"👤 Клиент: {entry['user_id']}\n"
            f"🛹 Сапборд: {entry['sapboard_name']}; id=({entry['sapboard_id']})\n"
            f"🧑‍💼 Админ: {entry['admin_name']} (ID: {entry['admin_id']})\n"
            f"📅 Начало: {entry['start']}\n"
            f"🕒 Длительность: {entry['duration']:.2f} ч.\n"
            f"💰 Стоимость: {entry['cost']:.2f} руб.\n"
            "───────────────\n"
        )

    if len(filtered) > 10:
        text += f"\n... и ещё {len(filtered) - 10} записей. Используйте фильтры для уточнения."

    await message.answer(text)


@dp.message(F.text == "Аренда доски")
async def btn_rent(message: Message, state: FSMContext):
    await cmd_rent(message, state)


@dp.message(F.text == "Статус")
async def btn_status(message: Message):
    await cmd_status(message)


@dp.message(F.text == "Помощь")
async def btn_help(message: Message):
    await cmd_help(message)


async def main():
    print("Ждём 30 секунд перед стартом, чтобы избежать конфликта...")
    time.sleep(30)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.info("Бот стартует...")
    database.init_db()
    asyncio.run(main())
