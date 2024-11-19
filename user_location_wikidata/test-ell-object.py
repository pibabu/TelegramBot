import os
from dotenv import load_dotenv
from typing import List
import telebot
import ell
from ell import Message, ContentBlock
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
        self.ttl = 60 * 60 * 24  # 24-hour expiry
        self.max_messages = 50

    def _get_key(self, chat_id: int) -> str:
        """Generate a Redis key for the given chat ID."""
        return f"chat:{chat_id}:messages"

    def add_message(self, chat_id: int, message: Message) -> None:
        key = self._get_key(chat_id)

        # Serialize the message for storage
        message_data = {
            "role": message.role,
            "content": message.text,
            "timestamp": datetime.now().isoformat(),
        }

        # Debug: Print serialized data
        print("Serialized message data:", message_data)

        # Push serialized data to Redis
        self.redis.lpush(key, json.dumps(message_data))
        self.redis.ltrim(key, 0, self.max_messages - 1)
        self.redis.expire(key, self.ttl)

    def get_history(self, chat_id: int) -> List[Message]:
        key = self._get_key(chat_id)
        messages = self.redis.lrange(key, 0, -1)  # List of JSON strings

        history = []
        for msg in reversed(messages):  # Reverse to get chronological order
            msg_data = json.loads(msg)  # Deserialize the message

            # Deserialize `content` back into a list of `ContentBlock` objects
            content_blocks = [
                ContentBlock(
                    parsed=cb.get("parsed"),
                    text=cb.get("text"),
                    tool_call=cb.get("tool_call"),
                    tool_result=cb.get("tool_result"),
                )
                for cb in json.loads(msg_data["content"])  # ############
            ]

            # Create a `Message` object
            history.append(
                Message(
                    role=msg_data["role"],
                    content=content_blocks,
                )
            )

        return history

    def clear_history(self, chat_id: int) -> None:
        """Clear message history for a chat."""
        key = self._get_key(chat_id)
        self.redis.delete(key)


# Initialize Redis manager
redis_manager = RedisMessageManager(REDIS_URL)


@ell.simple(model="gpt-4o-mini", temperature=0.7)
def chat_bot(history: List[Message], input_message: Message) -> Message:
    """Generate a response based on chat history and the new message."""
    # Here, `ell` will use the history to create a meaningful response.
    return Message(
        role="assistant",
        content=[ContentBlock(text="This is a placeholder response.")],
    )


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """Handle incoming text messages."""
    chat_id = message.chat.id
    user_message = Message(
        role="user",
        content=[ContentBlock(text=message.text)],
    )

    # Save user message to Redis
    redis_manager.add_message(chat_id, user_message)

    # Retrieve chat history
    history = redis_manager.get_history(chat_id)  ##############################

    # Generate bot response
    bot_response = chat_bot(history, user_message)

    # Save bot response to Redis
    redis_manager.add_message(chat_id, bot_response)

    # Send bot response back to the user
    response_text = "\n".join(cb.text for cb in bot_response.content if cb.text)
    bot.reply_to(message, response_text)


@bot.message_handler(commands=["clear"])
def handle_clear(message):
    """Handle the /clear command to clear chat history."""
    chat_id = message.chat.id
    redis_manager.clear_history(chat_id)
    bot.reply_to(message, "Chat history cleared!")


if __name__ == "__main__":
    print("Bot is running...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Error occurred: {e}")
