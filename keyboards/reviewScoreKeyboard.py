from telebot import types


def reviewScoreKeyboard():
    markup = types.InlineKeyboardMarkup(row_width=5)

    score_row = [
        types.InlineKeyboardButton("1", callback_data="review_score:1"),
        types.InlineKeyboardButton("2", callback_data="review_score:2"),
        types.InlineKeyboardButton("3", callback_data="review_score:3"),
        types.InlineKeyboardButton("4", callback_data="review_score:4"),
        types.InlineKeyboardButton("5", callback_data="review_score:5"),
    ]
    undecided_row = [types.InlineKeyboardButton("Не определился", callback_data="review_score:undecided")]
    back_row = [types.InlineKeyboardButton("Назад", callback_data="review_back")]

    markup.row(*score_row)
    markup.row(*undecided_row)
    markup.row(*back_row)
    return markup
