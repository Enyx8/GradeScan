from bot_instance import bot
from utils.getUserRole import getUserRole
from utils.getUserProfile import getUserProfile
from utils.addNewUser import addNewUser
from keyboards import main_menu_keyboard

registration_state = {}

def is_profile_complete(profile):
    if not profile: return False
    return all([profile.get("last_name"), profile.get("first_name"), 
                profile.get("team_name") != "-", profile.get("grade") != "-"])

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
    registration_state[message.from_user.id]["team"] = message.text
    sent = bot.send_message(message.chat.id, "Введите грейд и позицию (Junior Backend):")
    bot.register_next_step_handler(sent, reg_pos)

def reg_pos(message):
    state = registration_state.get(message.from_user.id)
    parts = message.text.split()
    if len(parts) != 2:
        sent = bot.send_message(message.chat.id, "Формат: Junior Backend. Попробуйте еще раз:")
        bot.register_next_step_handler(sent, reg_pos)
        return
    
    # Для целей тестирования добавлено скрытое присвоение роли менеджера
    role = "manager" if "manager" in parts[1].lower() else "employee"
    
    addNewUser(message.from_user.id, state["fn"], state["ln"], state["mn"], state["team"], parts[0], parts[1], role)
    bot.send_message(message.chat.id, "Регистрация завершена!", reply_markup=main_menu_keyboard(role))