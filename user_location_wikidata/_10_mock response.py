import os
from dotenv import load_dotenv
from typing import List
import telebot
import ell
from ell import Message

load_dotenv()
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
if not TELEGRAM_API_KEY:
    raise EnvironmentError("TELEGRAM_API_KEY is missing. Please check your .env file.")

bot = telebot.TeleBot(TELEGRAM_API_KEY)

ell.init(store="./logdir", autocommit=True, verbose=True)


@ell.simple(model="gpt-4o-mini", temperature=0.7)
def chat_bot(user_prompt, message_history: List[Message]) -> List[Message]:
    """unhelpfull assistant"""
    # return user_prompt + message_history
    return f"{message_history}\n{user_prompt}"


message_history = []


# SPARQL query generator
@ell.simple(
    model="gpt-4o-mini", n=3
)  # This means that when you call an ell.simple language model program with n greater than one, instead of returning a string, it returns a list of strings.
def generate_sparql_queries(coordinates: list, message_history: list):
    """
    You are an expert SPARQL-query generator for wikidata. You output three SPARQL queries based on user (intent, coordinates).
    think deeply about user objective and wikidata schema before giving answer.
    user coordinates and chat history:
    """
    return coordinates, message_history


# Mock Wikidata API call handler
def wikidata_api_calls(queries: list) -> list:
    """
    Mock implementation of API calls to Wikidata. Returns a list of mock responses.
    """
    mock_responses = [
        f"Mock response 1 for query: {queries[0]}",
        f"Mock response 2 for query: {queries[1]}",
        f"Mock response 3 for query: {queries[2]}",
    ]
    return mock_responses


# Response generator
@ell.simple(model="gpt-4o-mini")
def generate_final_response(context: list, message_history: list) -> str:
    """
    Generate a final response from Wikidata context data. evaluate context
    """
    return "\n".join(context), message_history


def pipeline(*funcs):
    def inner(data):
        result = data
        for func in funcs:
            result = func(result)
        return result

    return inner


wikidata_pipeline = pipeline(
    lambda x: (
        generate_sparql_queries(x[0], x[1]),
        x[1],
    ),
    # x is Tuple[List[float], List[Message]]
    # returns(queries, message_history)
    lambda x: (
        wikidata_api_calls(x[0]),
        x[1],
    ),
    # x is now List[str] (the SPARQL queries)
    # Returns List[str] (API results) and untouched history
    lambda x: generate_final_response(x[0], x[1]),
    # Returns str (final message)
)


# Telegram location handler
@bot.message_handler(content_types=["location"])
def handle_location(message):
    lat, lon = message.location.latitude, message.location.longitude
    coordinates = [lat, lon]
    response = wikidata_pipeline(coordinates)
    bot.send_message(message.chat.id, response)


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    message_history = []

    if message.text:
        user_message = ell.user(message.text)
        message_history.append(user_message)

        response = chat_bot(message.text, message_history)
        bot_response = ell.system(response)
        message_history.append(bot_response)

        bot.send_message(chat_id, response)

        # while True:
    # user_input = input("You: ")
    # message_history.append(ell.user(user_input))
    # response = chat_bot(message_history)
    # print("Bot:", response.text)
    # message_history.append(response)

    else:
        bot.reply_to(message, "Please send text or location only.")


# Main entry point
if __name__ == "__main__":
    print("Bot is running...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Error occurred: {e}")
