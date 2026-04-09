from telebot import types

def employee_menu_kb():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("👤 Мой профиль"), types.KeyboardButton("⭐ Оценить коллег"))
    return markup

def manager_menu_kb():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📊 Сотрудники команды"))
    return markup

def teammates_kb(teammates, completed_ids):
    markup = types.InlineKeyboardMarkup()

    for teammate in teammates:
        status = "✅ " if teammate['id'] in completed_ids else ""
        markup.add(types.InlineKeyboardButton(
            f"{status}{teammate['first_name']} {teammate['last_name']}", 
            callback_data=f"rate_user_{teammate['id']}"
        ))

    return markup

def skills_kb(skills, user_id):
    markup = types.InlineKeyboardMarkup()
    for skill in skills:
        markup.add(types.InlineKeyboardButton(skill['name_ru'], callback_data=f"skill_{user_id}_{skill['id']}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_teammates"))
    return markup

def score_kb(user_id, skill_id):
    markup = types.InlineKeyboardMarkup(row_width=5)
    btns = [types.InlineKeyboardButton(str(i), callback_data=f"set_{user_id}_{skill_id}_{i}") for i in range(1, 6)]

    markup.add(*btns)
    markup.add(types.InlineKeyboardButton("🤷 Затрудняюсь ответить", callback_data=f"set_{user_id}_{skill_id}_0"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"rate_user_{user_id}"))

    return markup