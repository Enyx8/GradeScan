# Сделан импорт TeleBot и Message, чтобы были подсказки (потом убрать)
from telebot import TeleBot
from telebot.types import Message
from utils.addNewUser import addNewUser

def registrationHandler(bot: TeleBot, message: Message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, "Добро пожаловать в бот по оценке компетенций GradeSkill! 👋\n\n" \
    "Для начала работы необходимо пройти регистрацию.")

    msg = bot.send_message(message.chat.id, "Введите Ваше **Имя**:")
    bot.register_next_step_handler(msg, readFirstName, bot)

def readFirstName(message: Message, bot: TeleBot):
    userFirstName = message.text

    if not userFirstName or len(userFirstName) < 2 or len(userFirstName) > 20:
        msg = bot.reply_to(message, "Введите корректное имя:")
        return bot.register_next_step_handler(msg, readFirstName, bot)
    
    msg = bot.send_message(message.chat.id, f"Приятно познакомиться, {userFirstName}! Теперь введите **Фамилию**:")
    bot.register_next_step_handler(msg, readLastName, bot, userFirstName)

def readLastName(message: Message, bot: TeleBot, userFirstName: str):
    userLastName = message.text

    if not userLastName or len(userLastName) < 2 or len(userLastName) > 20:
        msg = bot.reply_to(message, "Введите корректную фамилию:")
        return bot.register_next_step_handler(msg, userLastName, bot, userFirstName)
    
    msg = bot.send_message(message.chat.id, "Введите Ваше **Отчество**:")
    bot.register_next_step_handler(msg, completeRegistration, bot, userFirstName, userLastName)

def completeRegistration(message: Message, bot: TeleBot, userFirstName: str, userLastName: str):
    userMiddleName = message.text
    user_id = message.from_user.id

    addNewUser(user_id, userFirstName, userLastName, userMiddleName)
    
    from keyboards.checkRegistrationStatusKeyboard import checkRegistrationStatusKeyboard
    
    bot.send_message(
        message.chat.id, 
        "✅ Заявка принята! Данные отправлены на проверку администратору компании. Ожидайте подтверждения. 📝",
        reply_markup=checkRegistrationStatusKeyboard()
    )
