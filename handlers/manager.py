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
            
            # Получаем список сотрудников и кол-во аномалий
            query = """
                SELECT u.id, u.last_name, u.first_name, u.grade,
                (SELECT COUNT(*) FROM review r WHERE r.subject_id = u.id AND r.is_strange = TRUE) as anomalies
                FROM "user" u WHERE u.team_id = %s AND u.role = 'employee'
            """
            cursor.execute(query, (t_id,))
            members = cursor.fetchall()
            
            if not members:
                bot.send_message(message.chat.id, "В вашей команде пока нет сотрудников для оценки.")
                return

            text = "📋 **Сотрудники вашей команды:**\n\n"
            markup = types.InlineKeyboardMarkup()
            for m in members:
                anomaly_text = f" (⚠️ {m[4]} аном.)" if m[4] > 0 else " (✅ Ок)"
                text += f"• {m[1]} {m[2]} — `{m[3]}` {anomaly_text}\n"
                markup.add(types.InlineKeyboardButton(f"📊 Отчет: {m[1]}", callback_data=f"mgr_rpt:{m[0]}"))
            
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

    report = f"📊 **ОТЧЕТ АТТЕСТАЦИИ: {u_info[0]} {u_info[1]}**\n\n"
    report += f"🔹 Текущий грейд: `{u_info[2]}`\n"
    report += f"🔹 Позиция: `{result['position'].upper()}`\n"
    report += "──────────────────\n"
    
    for s_id, name, avg in result['stats']:
        report += f"📍 {name}: **{float(avg):.2f}**\n"
    
    report += "──────────────────\n"
    report += f"🚀 Рекомендация системы: **{result['recommended_grade']}**\n"
    
    if result['recommended_grade'] == u_info[2]:
        report += "\n✅ Сотрудник соответствует текущему грейду."
    elif result['recommended_grade'] == "Senior" and u_info[2] != "Senior":
        report += "\n🔥 Рекомендовано повышение!"
    elif result['recommended_grade'] == "Middle" and u_info[2] == "Junior":
        report += "\n🔥 Рекомендовано повышение до Middle!"
    
    bot.send_message(call.message.chat.id, report, parse_mode="Markdown")
    bot.answer_callback_query(call.id)