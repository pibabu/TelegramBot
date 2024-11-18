import os
from dotenv import load_dotenv
from typing import List
import telebot
import ell
from ell import Message

# Load environment variables
load_dotenv()
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
if not TELEGRAM_API_KEY:
    raise EnvironmentError("TELEGRAM_API_KEY is missing. Please check your .env file.")

bot = telebot.TeleBot(TELEGRAM_API_KEY)
ell.init(store="./logdir", autocommit=True, verbose=True)


# SPARQL query generator
@ell.simple(model="gpt-4o-mini", n=3)
def generate_sparql_queries(coordinates: list, message_history: list):
    """
    Generate three SPARQL queries based on user coordinates and chat history.
    """
    return coordinates, message_history


# API call handler
def wikidata_api_calls(queries: list) -> list:
    """
    Make API calls to Wikidata and return the responses.
    """
    results = []
    for query in queries:
        # Call Wikidata API (placeholder for actual implementation)
        results.append(f"Query result for: {query}")
    return results


# Response generator
@ell.simple(model="gpt-4o-mini")
def generate_final_response(context: list) -> str:
    """
    Generate a final response from Wikidata context data.
    """
    return "\n".join(context)


# Pipeline function
def pipeline(*funcs):
    def inner(data):
        result = data
        for func in funcs:
            result = func(result)
        return result

    return inner


wikidata_pipeline = pipeline(
    generate_sparql_queries,
    wikidata_api_calls,
    generate_final_response,
)


# Telegram location handler
@bot.message_handler(content_types=["location"])
def handle_location(message):
    lat, lon = message.location.latitude, message.location.longitude
    coordinates = [lat, lon]
    response = wikidata_pipeline(coordinates)
    bot.send_message(message.chat.id, response)


# Conversational chatbot
@ell.complex(model="gpt-4o-mini", temperature=0.7)
def chat_bot(message_history: List[Message]) -> List[Message]:
    return [
        ell.system("You are a friendly chatbot. Engage in casual conversation."),
    ] + message_history


# Main entry point
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()


@bot.message_handler(content_types=["location"])
def handle_location(message):
    """Handle location messages"""
    lat = message.location.latitude
    lon = message.location.longitude
    coordinates = f"{lat}, {lon}"

    response = wikidata_pipeline(coordinates)

    for query in response:
        bot.send_message(message.chat.id, query)


@ell.complex(model="gpt-4o-mini", temperature=0.7)
def chat_bot(message_history: List[Message]) -> List[Message]:
    return [
        ell.system("You are a friendly chatbot. Engage in casual conversation."),
    ] + message_history


message_history = []
while True:
    user_input = input("You: ")
    message_history.append(ell.user(user_input))
    response = chat_bot(message_history)
    print("Bot:", response.text)
    message_history.append(response)


@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handle all other messages."""
    if message.text:
        response = chatbot(message.text)
        for query in response:
            bot.send_message(message.chat.id, query)
    else:
        bot.reply_to(message, "Please send text or location only.")


if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
