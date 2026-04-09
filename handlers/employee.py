from bot_instance import bot
from keyboards import colleague_list_keyboard, skills_keyboard, score_keyboard
from utils.db_manager import get_team_members, save_review
from utils.getUserProfile import getUserProfile

@bot.message_handler(func=lambda m: m.text == "Профиль")
def show_profile(message):
    p = getUserProfile(message.from_user.id)
    if not p:
        bot.send_message(message.chat.id, "Профиль не найден. Пройдите регистрацию /start")
        return
    text = (f"Твой профиль:\nФИО: {p['last_name']} {p['first_name']}\n"
            f"Команда: {p['team_name']}\nГрейд: {p['grade']}\nПозиция: {p['position']}")
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "Оценить коллег")
def list_colleagues(message):
    members = get_team_members(message.from_user.id)
    if not members:
        bot.send_message(message.chat.id, "В вашей команде пока нет никого, кроме вас.")
        return
    bot.send_message(message.chat.id, "Выберите коллегу для оценки:", reply_markup=colleague_list_keyboard(members))

@bot.callback_query_handler(func=lambda c: c.data == "back_to_team")
def back_to_team(call):
    members = get_team_members(call.from_user.id)
    bot.edit_message_text("Выберите коллегу:", call.message.chat.id, call.message.message_id, reply_markup=colleague_list_keyboard(members))

@bot.callback_query_handler(func=lambda c: c.data.startswith("sel_user:"))
def select_skills(call):
    user_id = call.data.split(":")[1]
    bot.edit_message_text("Выберите компетенцию для оценки:", call.message.chat.id, call.message.message_id, reply_markup=skills_keyboard(user_id))

@bot.callback_query_handler(func=lambda c: c.data.startswith("sel_skill:"))
def select_score(call):
    parts = call.data.split(":")
    u_id, s_id = parts[1], parts[2]
    bot.edit_message_text("Какую оценку поставите (1-5)?", call.message.chat.id, call.message.message_id, reply_markup=score_keyboard(u_id, s_id))

@bot.callback_query_handler(func=lambda c: c.data.startswith("rate:"))
def perform_rate(call):
    # Формат: rate:subject_id:skill_id:score
    _, subject_id, skill_id, score = call.data.split(":")
    
    success = save_review(call.from_user.id, subject_id, skill_id, score)
    
    if success:
        bot.answer_callback_query(call.id, text="Оценка сохранена! ✅")
        # Возвращаем к списку навыков, чтобы человек мог оценить что-то еще
        bot.edit_message_text("Компетенция оценена. Выберите следующую или вернитесь назад:", 
                              call.message.chat.id, call.message.message_id, 
                              reply_markup=skills_keyboard(subject_id))
    else:
        bot.answer_callback_query(call.id, text="Ошибка при сохранении ❌")