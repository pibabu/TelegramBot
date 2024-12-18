import os
from dotenv import load_dotenv
import telebot
import ell

ell.init(store="./logdir", autocommit=True, verbose=True)


load_dotenv()
Telegram_API_Key = os.getenv("Telegram_API_Key")
chat_id = os.getenv("Telegram_chat_id")


bot = telebot.TeleBot(Telegram_API_Key)


@ell.simple(model="gpt-4o-mini", temperature=0.9)
def generate_haiku(usermessage: str, language: str = "french"):
    """Generate haiku based on user message and style/language."""
    return f"{usermessage} in {language} language"


@bot.message_handler(commands=["haiku"])
def handle_haiku(message):
    try:
        # Get everything after /haiku
        if " " not in message.text:
            bot.reply_to(
                message,
                "Please provide a theme for the haiku.\nExample: /haiku day in the zoo",
            )
            return

        theme = message.text.split(" ", 1)[1]  # Get everything after the first space

        # Generate and send haiku
        haiku_response = generate_haiku(theme)
        bot.reply_to(message, haiku_response)

    except Exception as e:
        bot.reply_to(
            message, f"Sorry, couldn't generate a haiku. Please try again. {str(e)}"
        )


if __name__ == "__main__":
    try:
        print("Bot is running...")
        bot.send_message(chat_id, text="Bot is up and running!")
        bot.infinity_polling()
    except Exception as e:
        print(f"Bot's down:{str(e)}")
