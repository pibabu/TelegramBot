import os
from dotenv import load_dotenv
import telebot
import ell

ell.init(store='./logdir', autocommit=True)


load_dotenv()
TELEGRAM_API_KEY = os.getenv("Telegram_API_Key")


bot = telebot.TeleBot(TELEGRAM_API_KEY)

@ell.simple(model="gpt-4o")
def generate_location_response(coordinates: str):
    """You are a knowledgeable local guide who provides interesting insights about locations. 
    Keep responses concise and engaging."""
    return f"Share an interesting fact or detail about this location: {coordinates}"

@ell.simple(model="gpt-4o")
def generate_chat_response(message: str):
    """You are a friendly and helpful assistant who engages in casual conversation. 
    Keep responses concise and natural."""
    return f"Respond to this message: {message}"

@bot.message_handler(content_types=['location'])
def handle_location(message):
    """Handle location messages"""
    lat = message.location.latitude
    lon = message.location.longitude
    coordinates = f"{lat}, {lon}"
    response = generate_location_response(coordinates)
    bot.reply_to(message, response)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handle all other messages"""
    if message.text:
        response = generate_chat_response(message.text)
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "Please send text or location only.")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()