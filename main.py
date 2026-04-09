import time
from bot_instance import bot
from telebot.apihelper import ApiTelegramException
from utils.db_manager import check_database_connection
from psycopg2 import Error as PsycopgError

import handlers.start
import handlers.employee
import handlers.manager

if __name__ == "__main__":
    try:
        check_database_connection()
        print("[DB] Connection successful")
    except PsycopgError as db_error:
        print(f"[DB] Connection failed: {db_error}")

    print("Бот запущен...")
    bot.remove_webhook()
    
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
        except ApiTelegramException as e:
            if "409" in str(e):
                print("[BOT] 409 Conflict. Retrying in 5s...")
                time.sleep(5)
                continue
            raise e