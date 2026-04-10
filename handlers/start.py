from telebot import types

from bot_instance import bot
from utils.getUserRole import getUserRole
from utils.getUserProfile import getUserProfile
from utils.addNewUser import addNewUser
from utils.db_manager import delete_user_by_telegram_id, promote_user_to_manager
from keyboards import main_menu_keyboard, registration_position_keyboard, registration_grade_keyboard

REG_POSITION_MAP = {
    "backend_jvm": ("backend", "employee"),
    "backend_py": ("backend", "employee"),
    "frontend": ("frontend", "employee"),
    "devops": ("devops", "employee"),
    "qa": ("qa", "employee"),
    "manager": ("admin", "manager"),
}

registration_state = {}

def is_profile_complete(profile):
    if not profile: return False
    return all([profile.get("last_name"), profile.get("first_name"), 
                profile.get("team_name") != "-", profile.get("grade") != "-"])

@bot.message_handler(commands=["manager"])
def manager_command_handler(message):
    tid = message.from_user.id
    user_role = getUserRole(tid)
    if user_role == "NaN":
        bot.send_message(
            message.chat.id,
            "Сначала пройдите регистрацию: /start",
        )
        return
    if user_role == "manager":
        bot.send_message(
            message.chat.id,
            "У вас уже роль менеджера.",
            reply_markup=main_menu_keyboard("manager"),
        )
        return
    if user_role != "employee":
        bot.send_message(
            message.chat.id,
            "Команда /manager доступна только сотрудникам (роль employee).",
        )
        return
    if promote_user_to_manager(tid):
        bot.send_message(
            message.chat.id,
            "✅ Вы переведены в роль **менеджера**. Доступны отчёты по команде и оценка сотрудников.",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard("manager"),
        )
    else:
        bot.send_message(
            message.chat.id,
            "Не удалось обновить роль. Попробуйте позже.",
        )


@bot.message_handler(func=lambda m: m.text == "Профиль")
def profile_handler(message):
    tid = message.from_user.id
    user_role = getUserRole(tid)
    if user_role == "NaN":
        bot.send_message(message.chat.id, "Профиль не найден. Нажмите /start.")
        return
    profile = getUserProfile(tid)
    if not profile:
        bot.send_message(message.chat.id, "Профиль не найден. Нажмите /start.")
        return
    role_label = "💼 Менеджер" if user_role == "manager" else "👨‍💻 Сотрудник"
    text = (
        "👤 **Ваш профиль**\n\n"
        f"**ФИО:** `{profile['last_name']} {profile['first_name']}`\n"
        f"**Роль:** {role_label}\n"
        f"**Грейд:** `{profile['grade']}`\n"
        f"**Команда:** `{profile['team_name']}`\n"
        f"**Направление:** `{profile['position']}`\n"
    )
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(user_role),
    )


@bot.message_handler(commands=["reset"])
def reset_handler(message):
    tid = message.from_user.id
    registration_state.pop(tid, None)
    if getUserRole(tid) == "NaN":
        bot.send_message(
            message.chat.id,
            "В базе нет вашего профиля. Можете начать с /start.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        return
    if delete_user_by_telegram_id(tid):
        bot.send_message(
            message.chat.id,
            "✅ Ваш профиль и связанные данные (оценки, аттестации с вами) удалены.\n"
            "Нажмите /start, чтобы пройти регистрацию заново.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
    else:
        bot.send_message(
            message.chat.id,
            "Не удалось удалить данные. Попробуйте позже или проверьте лог сервера.",
        )


@bot.message_handler(commands=["start"])
def start_handler(message):
    user_role = getUserRole(message.from_user.id)
    profile = getUserProfile(message.from_user.id)
    
    # Если пользователя нет в базе или профиль не заполнен до конца
    if user_role == "NaN" or not is_profile_complete(profile):
        text = (
            "👋 **Добро пожаловать в NEO 360!**\n\n"
            "Этот сервис помогает объективно оценить компетенции коллег.\n\n"
            "📍 **Регистрация:**\n"
            "Пожалуйста, введите свое ФИО полностью (через пробел):"
        )
        sent = bot.send_message(message.chat.id, text, parse_mode="Markdown")
        bot.register_next_step_handler(sent, reg_fio)
    else:
        role_name = "💼 Менеджер" if user_role == 'manager' else "👨‍💻 Сотрудник"
        
        text = (
            f"✅ **С возвращением, {profile['first_name']}!**\n\n"
            f"👤 Роль: `{role_name}`\n"
            f"📈 Грейд: `{profile['grade']}`\n"
            f"👥 Команда: `{profile['team_name']}`\n\n"
            "Выберите нужный пункт меню ниже 👇"
        )
        bot.send_message(
            message.chat.id, 
            text, 
            reply_markup=main_menu_keyboard(user_role), 
            parse_mode="Markdown"
        )

def reg_fio(message):
    parts = message.text.split()
    if len(parts) < 2:
        sent = bot.send_message(message.chat.id, "Укажите как минимум имя и фамилию.")
        bot.register_next_step_handler(sent, reg_fio)
        return
    registration_state[message.from_user.id] = {"ln": parts[0], "fn": parts[1], "mn": " ".join(parts[2:])}
    sent = bot.send_message(message.chat.id, "Введите номер команды (например: 101):")
    bot.register_next_step_handler(sent, reg_team)

def reg_team(message):
    tid = message.from_user.id
    registration_state[tid]["team"] = message.text.strip()
    bot.send_message(
        message.chat.id,
        "Выберите **направление** (позицию):",
        parse_mode="Markdown",
        reply_markup=registration_position_keyboard(),
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("reg_pos:"))
def registration_pick_position(call):
    bot.answer_callback_query(call.id)
    tid = call.from_user.id
    code = call.data.split(":", 1)[1]
    if code == "back":
        bot.edit_message_text(
            "Выберите **направление**:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=registration_position_keyboard(),
        )
        return
    if tid not in registration_state:
        bot.send_message(call.message.chat.id, "Сессия регистрации сброшена. Нажмите /start.")
        return
    if code not in REG_POSITION_MAP:
        bot.send_message(call.message.chat.id, "Неизвестная позиция. Нажмите /start.")
        return
    registration_state[tid]["pos_code"] = code
    bot.edit_message_text(
        "Выберите **грейд**:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=registration_grade_keyboard(),
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("reg_gr:"))
def registration_pick_grade(call):
    bot.answer_callback_query(call.id)
    tid = call.from_user.id
    grade = call.data.split(":", 1)[1]
    state = registration_state.get(tid)
    if not state or "pos_code" not in state:
        bot.send_message(call.message.chat.id, "Сессия регистрации сброшена. Нажмите /start.")
        return
    pos_code = state["pos_code"]
    position_text, role = REG_POSITION_MAP[pos_code]
    try:
        addNewUser(
            tid,
            state["fn"],
            state["ln"],
            state["mn"],
            state["team"],
            grade,
            position_text,
            role,
        )
        registration_state.pop(tid, None)
        bot.send_message(
            call.message.chat.id,
            "Регистрация завершена!",
            reply_markup=main_menu_keyboard(role),
        )
    except ValueError as err:
        bot.send_message(call.message.chat.id, f"Ошибка данных: {err}. Нажмите /start.")
    except Exception as err:
        bot.send_message(call.message.chat.id, f"Ошибка сохранения: {err}")