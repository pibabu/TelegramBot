import os
from dotenv import load_dotenv
from typing import List, Tuple
import telebot
import ell
from ell import Message
import redis
import json
from datetime import datetime

# Load environment variables
load_dotenv()
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

if not TELEGRAM_API_KEY:
    raise EnvironmentError("TELEGRAM_API_KEY is missing")

# Initialize bot and Redis
bot = telebot.TeleBot(TELEGRAM_API_KEY)
ell.init(store="./logdir", autocommit=True, verbose=True)


class RedisMessageManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.ttl = 60 * 60 * 24  # 24 hour expiry
        self.max_messages = 50

    def _get_key(self, chat_id: int) -> str:
        return f"chat:{chat_id}:messages"

    def add_message(self, chat_id: int, message: Message) -> None:
        key = self._get_key(chat_id)

        # Convert Message to dict for storage
        message_data = {
            "role": message.role,
            "content": str(message.content),  # Convert to string
            "timestamp": datetime.now().isoformat(),
        }

        # Add to Redis list
        self.redis.lpush(key, json.dumps(message_data))

        # Trim to max length
        self.redis.ltrim(key, 0, self.max_messages - 1)

        # Set expiry
        self.redis.expire(key, self.ttl)

    def get_history(self, chat_id: int) -> List[Message]:
        """Retrieve message history from Redis"""
        key = self._get_key(chat_id)
        messages = self.redis.lrange(key, 0, -1)

        # Convert stored messages back to Message objects
        return [
            Message(role=json.loads(msg)["role"], content=json.loads(msg)["content"])
            for msg in reversed(messages)  # Reverse to get chronological order
        ]


# Initialize Redis manager
redis_manager = RedisMessageManager(REDIS_URL)


@ell.simple(model="gpt-4o-mini", temperature=0.7)
def chat_bot(user_prompt: str, message_history: List[Tuple[str, str]]) -> str:
    """Chatbot with context awareness"""
    return [
        ell.system(f"""
                {user_prompt}.  
                Your goal is to come up with a response to a chat. Only"""),
        ell.user(format_message_history(message_history)),
    ]

def format_message_history(message_history: List[Tuple[str, str]]) -> str:
    return "\n".join([f"{name}: {message}" for name, message in message_history])


@ell.simple(model="gpt-4o-mini", n=3)
def generate_sparql_queries(coordinates: list, message_history: list):
    """
    You are an expert SPARQL-query generator for wikidata. You output three SPARQL queries based on user (intent, coordinates).
    think deeply about user objective and wikidata schema before giving answer.
    user coordinates and chat history:
    """
    return coordinates, message_history


def wikidata_api_calls(queries: list) -> list:
    """Mock Wikidata API calls"""
    return [f"Mock response for query: {query}" for query in queries]


@ell.simple(model="gpt-4o-mini")
def generate_final_response(context: list, message_history: list) -> str:
    """Generate final response using context and history"""
    return "\n".join(context)


def pipeline(*funcs):
    def inner(data):
        result = data
        for func in funcs:
            result = func(result)
        return result

    return inner


wikidata_pipeline = pipeline(
    lambda x: (generate_sparql_queries(x[0], x[1]), x[1]),
    lambda x: (wikidata_api_calls(x[0]), x[1]),
    lambda x: generate_final_response(x[0], x[1]),
)


@bot.message_handler(content_types=["location"])
def handle_location(message):
    """Handle location messages"""
    chat_id = message.chat.id
    lat, lon = message.location.latitude, message.location.longitude

    # Create location message
    location_msg = ell.user(f"Location shared: {lat}, {lon}")
    redis_manager.add_message(chat_id, location_msg)

    # Get message history
    history = redis_manager.get_history(chat_id)

    # Process through pipeline
    response = wikidata_pipeline(([lat, lon], history))

    # Store bot response
    bot_response = ell.system(response)
    redis_manager.add_message(chat_id, bot_response)

    bot.send_message(chat_id, response)


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """Handle text messages"""
    chat_id = message.chat.id

    def extract_text(text_content):
        user_message = ell.user(text_content)
        redis_manager.add_message(
            chat_id, user_message
        )  ##hier ist das problem?: user_message

        # Get updated history
        history = redis_manager.get_history(chat_id)

        # Generate response
        response = chat_bot(text_content, history)

        # Store bot response
        bot_response = ell.system(response)
        redis_manager.add_message(chat_id, bot_response)

        bot.send_message(chat_id, response)

    if message.text:
        extract_text(message.text)  # Call the extract_text function with message.text
    else:
        bot.reply_to(message, "Please send text or location only.")

    #     else:
    #         bot.reply_to(message, "Could not process your message.")
    # else:
    #     bot.reply_to(message, "Please send text or location only.")


@bot.message_handler(commands=["clear"])
def handle_clear(message):
    """Clear chat history command"""
    chat_id = message.chat.id
    redis_manager.clear_history(chat_id)
    bot.reply_to(message, "Chat history cleared!")


if __name__ == "__main__":
    print("Bot is running...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Error occurred: {e}")
