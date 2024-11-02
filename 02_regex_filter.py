import os
from dotenv import load_dotenv
import telebot


load_dotenv()
Telegram_API_Key=os.getenv("Telegram_API_Key")
chat_id=os.getenv("Telegram_chat_id")

bot = telebot.TeleBot(Telegram_API_Key) 

@bot.message_handler(commands=['start'])
def send_welcome(message):
	bot.reply_to(message, "Howdy, how are you doing?  Type /llm , /customize_me")
 
@bot.message_handler(regexp="///Beschwerde")
def say_hello(message):
    bot.reply_to(message, "Hey,ehhhh was.zisch ab")
    
@bot.message_handler(content_types=["location"])
def say_heyho(message):
    bot.reply_to(message, "dddddaa....hinter dir!")
    
bot.send_message(chat_id, text='app is up!')

    


bot.infinity_polling()