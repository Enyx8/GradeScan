from telebot.types import Message
from utils.addNewUser import addNewUser

def registrationHandler(bot, message: Message):
    user_id = message.from_user.id
    addNewUser(user_id)
    bot.reply_to(
        message,
        "Добро пожаловать в бот по оценке компетенций GradeSkill! 👋\n\n"
        "Вы являетесь новым пользователем, поэтому Вам необходимо дождать подтверждения регистрации администратором.\n\n"
        "Если Ваша регистрация будет подтверждена, бот отправит сообщение с дальнейшими инструкциями. 📝 "
    )