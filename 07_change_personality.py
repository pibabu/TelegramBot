import os
from dotenv import load_dotenv
import telebot
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from character_examples import PERSONALITIES
# from langchain.globals import set_verbose

load_dotenv()
TELEGRAM_API_KEY = os.getenv("Telegram_API_Key")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_API_KEY)


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# Global variable to store current personality for each user
user_personalities: Dict[int, str] = {}


def format_examples(personality_data: Dict) -> str:
    examples = personality_data["examples"]
    formatted = "\nExamples:\n"
    for ex in examples:
        formatted += f"User: {ex['user']}\nAssistant: {ex['bot']}\n\n"
    return formatted


def get_personality_data(personality: str) -> Dict:
    for p in PERSONALITIES:
        if p["personality"] == personality:
            return p
    return None


def generate_chat_response(user_id: int, message: str) -> str:
    personality = user_personalities.get(
        user_id, "business-bro"
    )  # default to business-bro
    personality_data = get_personality_data(personality)

    if not personality_data:
        return "Personality not found!"

    system_prompt = (  # noch checken
        f"{personality_data['description']}\n"
        f"{format_examples(personality_data)}\n"
        "Respond to the user's message in this style."
    )

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=message)]

    response = llm.invoke(messages)
    return response.content


@bot.message_handler(commands=["business-bro", "sad", "creepy"])
def set_mood(message):
    personality = message.text[1:]  # Remove the '/' from the command
    user_id = message.from_user.id

    if personality in [p["personality"] for p in PERSONALITIES]:
        user_personalities[user_id] = personality
        personality_data = get_personality_data(personality)
        response = (
            f"Switching to {personality} mode!\n{personality_data['description']}"
        )
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "Sorry, i don't know that personaity!")


@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handle all other messages"""
    if message.text:
        user_id = message.from_user.id
        response = generate_chat_response(user_id, message.text)
        bot.send_message(message.chat.id, response)
    else:
        bot.reply_to(message, "Please send text only.")


def get_current_personality(message) -> Dict[str, Any]:
    user_id = message.from_user.id
    return {"personality": user_personalities.get(user_id, "business-bro")}


if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
