import os
from dotenv import load_dotenv
from typing import List, Dict
import telebot
import ell
from ell import Message, ContentBlock
import redis
from datetime import datetime
from collections import defaultdict
import uuid

# Load environment variables
load_dotenv()
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

if not TELEGRAM_API_KEY:
    raise EnvironmentError("TELEGRAM_API_KEY is missing")

# Initialize bot and Redis
bot = telebot.TeleBot(TELEGRAM_API_KEY)
ell.init(store="./logdir", autocommit=True, verbose=True)


def serialize_message(message):
    return {
        "id": str(uuid.uuid4()),  # Unique identifier
        "role": message.role,  # system/user/assistant
        "text": message.text_only,  # Just the text content
        "timestamp": datetime.now().isoformat(),
    }


def deserialize_message(data):
    # Reconstruct basic Message object
    return ell.Message(role=data["role"], content=[ContentBlock(text=data["text"])])


class ChatManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.ttl = 60 * 60 * 24  # 24-hour expiry
        self.max_messages = 50
        # In-memory storage for active chats
        # self.active_chats: Dict[int, List[Message]] = defaultdict(list)

    def _get_key(self, chat_id: int) -> str:
        return f"chat:{chat_id}:active"

    def add_message(self, chat_id: int, message: Message) -> None:
        """Add message to both in-memory and Redis storage"""
        # Add to in-memory list
        # self.active_chats[chat_id].append(message)

        # Trim in-memory list if needed
        if len(self.active_chats[chat_id]) > self.max_messages:
            self.active_chats[chat_id] = self.active_chats[chat_id][
                -self.max_messages :
            ]

        # Update Redis activity timestamp
        key = self._get_key(chat_id)
        self.redis.set(key, "active", ex=self.ttl)

    def get_history(self, chat_id: int) -> List[Message]:
        """Get message history for a chat"""
        # Check if chat is in memory
        if chat_id in self.active_chats:
            return self.active_chats[chat_id]
        return []

    def clear_history(self, chat_id: int) -> None:
        """Clear chat history"""
        # Clear in-memory
        if chat_id in self.active_chats:
            del self.active_chats[chat_id]

        # Clear Redis activity marker
        key = self._get_key(chat_id)
        self.redis.delete(key)


# Initialize chat manager
chat_manager = ChatManager(REDIS_URL)


@ell.complex(model="gpt-4o-mini", temperature=0.7)
def chat_bot(history: List[Message], input_message: Message) -> Message:
    """Generate a response using the complete message history"""
    # Prepare the context with system prompt and full history
    return [
        ell.system(
            "You are a helpful assistant. Be concise and direct in your responses."
        ),
        *history,  # Include the entire existing conversation history
        input_message,  # Add the most recent input message
    ]


print("Message Object:", {Message})


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """Handle incoming text messages"""
    chat_id = message.chat.id

    # Create ell Message from telegram message
    user_message = ell.user(message.text)

    # Get complete history
    history = chat_manager.get_history(chat_id)

    # Generate bot response
    response = chat_bot(history, user_message)

    # Prepare response message (assistant message)
    assistant_response = ell.assistant(response.text)

    # Add messages to chat history
    chat_manager.add_message(chat_id, user_message)
    chat_manager.add_message(chat_id, assistant_response)

    # Send response to user
    bot.send_message(message.chat.id, assistant_response.text)  #####send_messsage statt


@bot.message_handler(commands=["clear"])
def handle_clear(message):
    """Handle the /clear command"""
    chat_id = message.chat.id
    chat_manager.clear_history(chat_id)
    bot.reply_to(message, "Chat history cleared!")


if __name__ == "__main__":
    print("Bot is running...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Error occurred: {e}")
