import telebot
from dotenv import load_dotenv
import os
import time
from telebot import apihelper
from telebot.apihelper import ApiTelegramException
from psycopg2 import Error as PsycopgError
from utils.getUserRole import getUserRole
from utils.db import check_database_connection
from utils.addNewUser import addNewUser
from utils.getUserProfile import getUserProfile
from keyboards.mainMenuKeyboard import mainMenuKeyboard
from keyboards.reviewScoreKeyboard import reviewScoreKeyboard

load_dotenv()
apihelper.ENABLE_MIDDLEWARE = True
registration_state = {}

try:
    check_database_connection()
except PsycopgError as db_error:
    print(f"[DB] Connection failed: {db_error}")

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_API"))


def is_profile_complete(profile):
    if profile is None:
        return False
    return all(
        [
            profile.get("last_name"),
            profile.get("first_name"),
            profile.get("team_name") and profile.get("team_name") != "-",
            profile.get("grade") and profile.get("grade") != "-",
            profile.get("position") and profile.get("position") != "-",
        ]
    )


def show_main_menu(chat_id, user_role, first_time=False):
    if user_role == "NaN":
        sent = bot.send_message(
            chat_id,
            "Привет! Для регистрации введи ФИО одним сообщением.\n"
            "Пример: Иванов Иван Иванович",
        )
        bot.register_next_step_handler(sent, registration_fio_handler)
    elif user_role in ("unregistered", "employee"):
        message_text = "Главное меню сотрудника"
        if first_time:
            message_text = "Регистрация завершена ✅\nГлавное меню сотрудника"
        bot.send_message(chat_id, message_text, reply_markup=mainMenuKeyboard())
    elif user_role == "manager":
        bot.send_message(chat_id, "Главное меню руководителя")
    elif user_role == "admin":
        bot.send_message(chat_id, "Главное меню администратора")


@bot.message_handler(commands=["start"])
def mainMenu(message):
    user_role = getUserRole(message.from_user.id)
    profile = getUserProfile(message.from_user.id)
    if user_role in ("unregistered", "employee") and not is_profile_complete(profile):
        show_main_menu(message.chat.id, "NaN")
        return
    show_main_menu(message.chat.id, user_role)


def registration_fio_handler(message):
    if not message.text or message.text.startswith("/"):
        bot.send_message(message.chat.id, "Регистрация отменена. Нажми /start и введи ФИО.")
        return

    fio_parts = message.text.strip().split()
    if len(fio_parts) < 2:
        bot.reply_to(
            message,
            "Нужно минимум 2 слова: Фамилия и Имя.\nПример: Иванов Иван Иванович",
        )
        sent = bot.send_message(message.chat.id, "Введи ФИО заново:")
        bot.register_next_step_handler(sent, registration_fio_handler)
        return

    last_name = fio_parts[0]
    first_name = fio_parts[1]
    middle_name = " ".join(fio_parts[2:]) if len(fio_parts) > 2 else None

    registration_state[message.from_user.id] = {
        "last_name": last_name,
        "first_name": first_name,
        "middle_name": middle_name,
    }
    sent = bot.send_message(
        message.chat.id,
        "Введи номер команды (например: 101)",
    )
    bot.register_next_step_handler(sent, registration_team_handler)


def registration_team_handler(message):
    if not message.text or message.text.startswith("/"):
        bot.send_message(message.chat.id, "Регистрация отменена. Нажми /start и начни заново.")
        return

    team_name = message.text.strip()
    if len(team_name) < 1:
        sent = bot.send_message(message.chat.id, "Команда не может быть пустой. Введи снова:")
        bot.register_next_step_handler(sent, registration_team_handler)
        return

    state = registration_state.get(message.from_user.id)
    if state is None:
        bot.send_message(message.chat.id, "Сессия регистрации истекла. Нажми /start.")
        return

    state["team_name"] = team_name
    sent = bot.send_message(
        message.chat.id,
        "Введи грейд и позицию через пробел.\n"
        "Пример: junior backend",
    )
    bot.register_next_step_handler(sent, registration_position_handler)


def registration_position_handler(message):
    if not message.text or message.text.startswith("/"):
        bot.send_message(message.chat.id, "Регистрация отменена. Нажми /start и начни заново.")
        return

    state = registration_state.get(message.from_user.id)
    if state is None:
        bot.send_message(message.chat.id, "Сессия регистрации истекла. Нажми /start.")
        return

    parts = message.text.strip().split()
    if len(parts) != 2:
        sent = bot.send_message(
            message.chat.id,
            "Неверный формат. Введи в формате: junior backend",
        )
        bot.register_next_step_handler(sent, registration_position_handler)
        return

    grade_text, position_text = parts[0], parts[1]
    try:
        addNewUser(
            telegramID=message.from_user.id,
            first_name=state["first_name"],
            last_name=state["last_name"],
            middle_name=state["middle_name"],
            team_name=state["team_name"],
            grade_text=grade_text,
            position_text=position_text,
            role="employee",
        )
        registration_state.pop(message.from_user.id, None)
        show_main_menu(message.chat.id, "employee", first_time=True)
    except ValueError:
        sent = bot.send_message(
            message.chat.id,
            "Не понял грейд/позицию. Пример: junior backend",
        )
        bot.register_next_step_handler(sent, registration_position_handler)
    except PsycopgError as db_error:
        bot.send_message(message.chat.id, f"Ошибка при сохранении в БД: {db_error}")


@bot.message_handler(func=lambda message: message.text == "Оценить коллег")
def start_colleague_review(message):
    bot.send_message(
        message.chat.id,
        "Выбран сотрудник: Тестовый коллега\nВыбери оценку по компетенции:",
        reply_markup=reviewScoreKeyboard(),
    )

@bot.message_handler(func=lambda message: message.text == "Профиль")
def show_profile(message):
    profile = getUserProfile(message.from_user.id)
    if profile is None:
        bot.send_message(message.chat.id, "Профиль не найден. Нажми /start для регистрации.")
        return

    fio = f"{profile['last_name']} {profile['first_name']} {profile['middle_name']}".strip()
    bot.send_message(
        message.chat.id,
        "Твой профиль:\n"
        f"ФИО: {fio}\n"
        f"Команда: {profile['team_name']}\n"
        f"Грейд: {profile['grade']}\n"
        f"Позиция: {profile['position']}\n"
        "Средняя оценка за последнюю аттестацию: пока нет данных",
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("review_score:"))
def review_score_handler(call):
    bot.answer_callback_query(call.id)
    score_value = call.data.split(":", 1)[1]
    if score_value == "undecided":
        text = "Оценка сохранена: Не определился"
    else:
        text = f"Оценка сохранена: {score_value}"

    bot.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=reviewScoreKeyboard(),
    )


@bot.callback_query_handler(func=lambda call: call.data == "review_back")
def review_back_handler(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "Список сотрудников команды:\n- Тестовый коллега ✅",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
    )

bot.remove_webhook()
while True:
    try:
        bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
    except ApiTelegramException as telegram_error:
        if "409" in str(telegram_error):
            print("[BOT] 409 Conflict: обнаружен второй экземпляр бота. Повтор через 5 секунд...")
            time.sleep(5)
            continue
        raise