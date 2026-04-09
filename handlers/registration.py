# Сделан импорт TeleBot и Message, чтобы были подсказки (потом убрать)
from telebot import TeleBot
from telebot.types import Message

def registrationHandler(bot: TeleBot):
    @bot.message_handler(commands=['start'])
    def registrationMessage(message: Message):
        user_id = message.from_user.id
        bot.reply_to(message, "Добро пожаловать в бот по оценке компетенций GradeSkill! 👋\n\n" \
        "Вы являетесь новым пользователем, поэтому Вам необходимо дождать подтверждения регистрации администратором.\n\n" \
        "Если Ваша регистрация будет подтверждена, бот отправит сообщение с дальнейшими инструкциями. 📝 ")