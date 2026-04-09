from telebot import types

def mainMenuKeyboard():
    markup = types.ReplyKeyboardMarkup()

    keyboardButton1 = types.KeyboardButton("Профиль")
    keyboardButton2 = types.KeyboardButton("Оценить коллег")

    markup.add(keyboardButton1, keyboardButton2)

    return markup