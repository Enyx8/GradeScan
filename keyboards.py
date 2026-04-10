from telebot import types

from utils.db_manager import list_skills_for_subject, rated_skill_ids_for_reviewer


def main_menu_keyboard(role):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if role == 'manager':
        markup.row("Сотрудники команды", "Профиль")
        markup.add("Оценить коллег")
    else:
        markup.row("Оценить коллег", "Профиль")
    return markup

def colleague_list_keyboard(members):
    markup = types.InlineKeyboardMarkup()
    for m in members:
        cap = min(m.get("skills_target") or 0, 8)
        if cap == 0:
            cap = 1
        status = "✅" if m["skills_rated"] >= cap else "⏳"
        markup.add(types.InlineKeyboardButton(
            f"{m['last_name']} {m['first_name']} {status}", 
            callback_data=f"sel_user:{m['id']}"
        ))
    return markup

def registration_position_keyboard():
    markup = types.InlineKeyboardMarkup()
    rows = [
        ("Backend (Java / Kotlin)", "reg_pos:backend_jvm"),
        ("Backend (Python)", "reg_pos:backend_py"),
        ("Frontend (React)", "reg_pos:frontend"),
        ("DevOps", "reg_pos:devops"),
        ("Data Science / QA", "reg_pos:qa"),
        ("Менеджер", "reg_pos:manager"),
    ]
    for label, data in rows:
        markup.add(types.InlineKeyboardButton(label, callback_data=data))
    return markup


def registration_grade_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("Junior", callback_data="reg_gr:Junior"),
        types.InlineKeyboardButton("Middle", callback_data="reg_gr:Middle"),
        types.InlineKeyboardButton("Senior", callback_data="reg_gr:Senior"),
    )
    markup.add(types.InlineKeyboardButton("⬅️ Назад к выбору направления", callback_data="reg_pos:back"))
    return markup


def skills_keyboard(subject_id, reviewer_tg_id=None):
    markup = types.InlineKeyboardMarkup()
    sid = int(subject_id)
    rated = (
        rated_skill_ids_for_reviewer(reviewer_tg_id, sid)
        if reviewer_tg_id is not None
        else set()
    )
    for s_id, s_name in list_skills_for_subject(sid):
        label = f"✅ {s_name}" if s_id in rated else s_name
        markup.add(
            types.InlineKeyboardButton(
                label, callback_data=f"sel_skill:{subject_id}:{s_id}"
            )
        )
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