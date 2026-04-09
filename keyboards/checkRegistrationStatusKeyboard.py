from telebot import types

def checkRegistrationStatusKeyboard():
    markup = types.InlineKeyboardMarkup()
    keyboardButton = types.InlineKeyboardButton("🔄 Проверить статус", callback_data="backToMainMenu")
    markup.add(keyboardButton)

    return markup