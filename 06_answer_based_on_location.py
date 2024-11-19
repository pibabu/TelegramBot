import os
from dotenv import load_dotenv
import telebot
import ell

ell.init(store="./logdir", autocommit=True)


load_dotenv()
TELEGRAM_API_KEY = os.getenv("Telegram_API_Key")


bot = telebot.TeleBot(TELEGRAM_API_KEY)


@ell.simple(model="gpt-4o-mini")
def generate_location_response(coordinates: str):
    """You are local guide.if there's nothing going on, zoom out a bit to a better story"""
    return f"Share an interesting fact or detail about this location: {coordinates}"


@ell.simple(model="gpt-4o-mini")
def generate_chat_response(message: str):
    """You are a unhelpful assistant.
    Keep responses concise:"""
    return message


@bot.message_handler(content_types=["location"])
def handle_location(message):
    """Handle location messages"""
    lat = message.location.latitude
    lon = message.location.longitude
    coordinates = f"{lat}, {lon}"
    response = generate_location_response(coordinates)
    bot.send_message(message.chat.id, response)


@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handle all other messages"""
    if message.text:
        response = generate_chat_response(message.text)
        bot.send_message(message.chat.id, response)
    else:
        bot.reply_to(message, "Please send text or location only.")


if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()


# while True:
#     user_input = input("You: ")
#     message_history.append(ell.user(user_input))
#     response = chat_bot(message_history)
#     print("Bot:", response.text)
#     message_history.append(response)

#     break
