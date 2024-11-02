import os
from dotenv import load_dotenv
import telebot

load_dotenv()

Telegram_API_Key=os.getenv("Telegram_API_Key")

bot = telebot.TeleBot(Telegram_API_Key, parse_mode=None) # You can set parse_mode by default. HTML or MARKDOWN

@bot.message_handler(commands=['start'])
def send_welcome(message):
	bot.reply_to(message, "Howdy, how are you doing?  Type /llm ")
 
@bot.message_handler(commands=["//Beschwerde"])
def say_hello(message):
    bot.reply_to(message, "Hey,ehhhh was.zisch ab")
    
@bot.message_handler(commands=["customize_me"])
def say_heyho(message):
    bot.reply_to(message, "heyho")

    

@bot.message_handler(func=lambda message: True)
def echo_all(message):
	bot.reply_to(message, message.text)

bot.infinity_polling()