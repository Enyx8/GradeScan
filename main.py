import telebot
from dotenv import load_dotenv
import os
from telebot import apihelper
from utils.getUserRole import getUserRole
from handlers.registration import registrationHandler
from keyboards.checkRegistrationStatusKeyboard import checkRegistrationStatusKeyboard

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
	if message.userRole == "NaN":
		registrationHandler(bot)
	elif message.userRole == "unregistered":
		bot.send_message(message.chat.id, "Ваша заявка на регистрацию в сервисе ожидает подиверждения, ожидайте ⏳", reply_markup=checkRegistrationStatusKeyboard())
	elif message.userRole == "employee":
		bot.reply_to(message, "Employee")
	elif message.userRole == "manager":
		bot.reply_to(message, "Manager")
	elif message.userRole == "admin":
		bot.reply_to(message, "Admin")

@bot.callback_query_handler(func=lambda call: call.data == "backToMainMenu")
def backToMainMenu_handler(call):
    bot.answer_callback_query(call.id)
    mainMenu(call.message) 

bot.infinity_polling()