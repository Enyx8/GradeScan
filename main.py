import telebot
from dotenv import load_dotenv
import os
from telebot import apihelper
from utils.getUserRole import getUserRole

load_dotenv()
apihelper.ENABLE_MIDDLEWARE = True

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_API"))

@bot.middleware_handler(update_types=["message", "callback_query"])
def addUserRole(bot, update):
	if hasattr(update, 'message'):
		message = update.message
	else:
		message = update 
	
	message.userRole = getUserRole(message.from_user.id)

@bot.message_handler(commands=['start'])
def mainMenu(message):
	if message.userRole == "employee":
		bot.send_message(message.chat.id, "Employee")
	elif message.userRole == "manager":
		bot.send_message(message.chat.id, "Manager")
	elif message.userRole == "admin":
		bot.send_message(message.chat.id, "Admin")

@bot.callback_query_handler(func=lambda call: call.data == "backToMainMenu")
def backToMainMenu_handler(call):
    bot.answer_callback_query(call.id)
    mainMenu(call.message) 

bot.infinity_polling()