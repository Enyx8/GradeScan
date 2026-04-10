from bot_instance import bot
from utils.db_manager import get_connection
from telebot import types
from utils.calculations import calculate_grade_conclusion

@bot.message_handler(func=lambda m: m.text == "Сотрудники команды")
def team_report(message):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Получаем команду менеджера
            cursor.execute('SELECT team_id FROM "user" WHERE telegram_id = %s', (message.from_user.id,))
            res = cursor.fetchone()
            if not res:
                bot.send_message(message.chat.id, "Вы не зарегистрированы как менеджер.")
                return
            t_id = res[0]

            query = """
                SELECT u.id, u.last_name, u.first_name, u.grade,
                (SELECT COUNT(*) FROM review r
                 WHERE r.subject_id = u.id AND r.is_strange = TRUE) AS anomalies,
                (SELECT COUNT(*) FROM review r
                 WHERE r.subject_id = u.id
                   AND r.score IS NOT NULL
                   AND r.is_strange = FALSE) AS usable_scores
                FROM "user" u WHERE u.team_id = %s AND u.role = 'employee'
            """
            cursor.execute(query, (t_id,))
            members = cursor.fetchall()
            
            if not members:
                bot.send_message(message.chat.id, "В вашей команде пока нет сотрудников для оценки.")
                return

            text = (
                "📋 **Сотрудники вашей команды:**\n\n"
                "_✅ Ок — по сотруднику уже есть нормальные оценки для отчёта; "
                "⏳ — пока нет оценок; ⚠️ — есть отмеченные аномалии._\n\n"
            )
            markup = types.InlineKeyboardMarkup()
            for m in members:
                anomalies = m[4]
                usable_scores = m[5] or 0
                if usable_scores == 0:
                    status_text = " (⏳ Пока нет оценок)"
                elif anomalies > 0:
                    status_text = f" (⚠️ {anomalies} аном.)"
                else:
                    status_text = " (✅ Ок)"
                text += f"• {m[1]} {m[2]} — `{m[3]}`{status_text}\n"
                full_name = f"{m[1]} {m[2]}".strip()
                btn_label = f"📊 Отчёт: {full_name}"
                if len(btn_label) > 64:
                    btn_label = btn_label[:61] + "…"
                markup.add(types.InlineKeyboardButton(btn_label, callback_data=f"mgr_rpt:{m[0]}"))
            
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
    finally:
        conn.close()

@bot.callback_query_handler(func=lambda c: c.data.startswith("mgr_rpt:"))
def detailed_report(call):
    u_id = int(call.data.split(":")[1])
    
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT last_name, first_name, grade FROM "user" WHERE id = %s', (u_id,))
            u_info = cursor.fetchone()
    finally:
        conn.close()

    result = calculate_grade_conclusion(u_id)
    
    if not result:
        bot.answer_callback_query(call.id, "Недостаточно данных для формирования отчета")
        bot.send_message(call.message.chat.id, f"У сотрудника {u_info[0]} пока нет оценок.")
        return

    report = f"📊 **Отчёт по последней аттестации: {u_info[0]} {u_info[1]}**\n\n"
    report += f"🔹 Текущий грейд: `{u_info[2]}`\n"
    report += f"🔹 Позиция: `{result['position'].upper()}`\n"
    report += "──────────────────\n"
    
    for s_id, name, avg in result['stats']:
        report += f"📍 {name}: **{float(avg):.2f}**\n"
    
    report += "──────────────────\n"
    report += f"🚀 Рекомендация системы: **{result['recommended_grade']}**\n"

    cur = u_info[2]
    rec = result["recommended_grade"]
    rank = {"Intern": 0, "Junior": 1, "Middle": 2, "Senior": 3, "Lead": 4}
    r_cur = rank.get(cur, 1)
    r_rec = rank.get(rec, 0)

    if rec == cur:
        report += "\n✅ Сотрудник соответствует текущему грейду (по матрице компетенций)."
    elif r_rec > r_cur:
        report += f"\n🔥 Рекомендовано повышение до **{rec}**."
    elif r_rec < r_cur:
        report += (
            f"\n⚠️ По матрице ближе к уровню **{rec}**, чем к текущему **{cur}**. "
            "Это не повышение: при низких оценках стоит пересмотреть соответствие грейду."
        )
    else:
        report += f"\n📌 Сравните рекомендацию **{rec}** с текущим грейдом **{cur}** на кадровой встрече."
    
    bot.send_message(call.message.chat.id, report, parse_mode="Markdown")
    bot.answer_callback_query(call.id)