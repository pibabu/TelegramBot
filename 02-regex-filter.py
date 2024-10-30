import os
from dotenv import load_dotenv
import telebot

load_dotenv()

bot = telebot.TeleBot("Telegram_API_Key", parse_mode=None)