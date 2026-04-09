from telebot import types

def main_menu_keyboard(role):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if role == 'manager':
        markup.add("Сотрудники команды", "Профиль")
    else:
        markup.add("Оценить коллег", "Профиль")
    return markup

def colleague_list_keyboard(members):
    markup = types.InlineKeyboardMarkup()
    for m in members:
        # Считаем, что оценка завершена, если оценены хотя бы 4 навыка
        status = "✅" if m['skills_rated'] >= 4 else "⏳"
        markup.add(types.InlineKeyboardButton(
            f"{m['last_name']} {m['first_name']} {status}", 
            callback_data=f"sel_user:{m['id']}"
        ))
    return markup

def skills_keyboard(subject_id):
    markup = types.InlineKeyboardMarkup()
    # В идеале тянуть из БД, но для хакатона фиксируем
    skills = [ (1, "Postgres"), (2, "Java"), (3, "Testing"), (4, "Soft skills") ]
    for s_id, s_name in skills:
        markup.add(types.InlineKeyboardButton(s_name, callback_data=f"sel_skill:{subject_id}:{s_id}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад к списку", callback_data="back_to_team"))
    return markup

def score_keyboard(subject_id, skill_id):
    markup = types.InlineKeyboardMarkup(row_width=5)
    # Кнопки 1-5
    scores = [types.InlineKeyboardButton(str(i), callback_data=f"rate:{subject_id}:{skill_id}:{i}") for i in range(1, 6)]
    markup.row(*scores)
    # Кнопка Затрудняюсь (ТЗ Сценарий 1)
    markup.add(types.InlineKeyboardButton("❓ Затрудняюсь ответить", callback_data=f"rate:{subject_id}:{skill_id}:undecided"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад к навыкам", callback_data=f"sel_user:{subject_id}"))
    return markup