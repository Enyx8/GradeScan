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
    
    if user_role == "NaN" or not is_profile_complete(profile):
        sent = bot.send_message(message.chat.id, "Привет! Для регистрации введи ФИО:\nПример: Иванов Иван Иванович")
        bot.register_next_step_handler(sent, reg_fio)
    else:
        bot.send_message(message.chat.id, f"Главное меню ({user_role})", reply_markup=main_menu_keyboard(user_role))

def reg_fio(message):
    parts = message.text.split()
    if len(parts) < 2:
        sent = bot.send_message(message.chat.id, "Минимум Фамилия и Имя. Введи заново:")
        bot.register_next_step_handler(sent, reg_fio)
        return
    registration_state[message.from_user.id] = {"ln": parts[0], "fn": parts[1], "mn": " ".join(parts[2:])}
    sent = bot.send_message(message.chat.id, "Введи номер команды (например: 101):")
    bot.register_next_step_handler(sent, reg_team)

def reg_team(message):
    registration_state[message.from_user.id]["team"] = message.text
    sent = bot.send_message(message.chat.id, "Введи грейд и позицию (junior backend):")
    bot.register_next_step_handler(sent, reg_pos)

def reg_pos(message):
    state = registration_state.get(message.from_user.id)
    parts = message.text.split()
    if len(parts) != 2:
        sent = bot.send_message(message.chat.id, "Формат: junior backend. Попробуй еще раз:")
        bot.register_next_step_handler(sent, reg_pos)
        return
    
    # Определяем роль менеджера для теста (например по секретному слову в позиции)
    role = "manager" if "manager" in parts[1].lower() else "employee"
    
    addNewUser(message.from_user.id, state["fn"], state["ln"], state["mn"], state["team"], parts[0], parts[1], role)
    bot.send_message(message.chat.id, "Регистрация завершена!", reply_markup=main_menu_keyboard(role))