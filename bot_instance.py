import os
import telebot
from dotenv import load_dotenv
from telebot import apihelper

load_dotenv()
token = os.getenv("TELEGRAM_BOT_API")
bot = telebot.TeleBot(token)