import os
from dotenv import load_dotenv
import telebot
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from character_examples import PERSONALITIES
from _09_state_management_models import ChatBotState

load_dotenv()
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class TelegramBot:
    def __init__(self):
        self.bot = telebot.TeleBot(TELEGRAM_API_KEY)
        self.llm = ChatOpenAI(temperature=0.7)
        self.state = ChatBotState(PERSONALITIES)
       # self.user_id = None 
        self.setup_handlers()
        
        
    def generate_chat_response(self, user_id: int, message: str) -> str:
        user_state = self.state.get_user_state(user_id)
        personality = self.state.get_personality(user_state.current_personality)
        
        if not personality:
            return "Personality not found!"
        
        system_prompt = (
            f"{personality.description}\n"
            f"{personality.format_examples()}\n"
            "Respond to the user's message in this style. be a helpfull assistant"
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=message)
        ]
        
        response = self.llm.invoke(messages)
        user_state.add_to_history(message, response.content)
        return response.content
    
    def handle_personality_command(self, message):
        personality = message.text[1:]  # Remove the '/' from the command
        user_id = message.from_user.id
        
        if self.state.update_user_personality(user_id, personality):
            personality_data = self.state.get_personality(personality)
            response = f"Switching to {personality} mode!\n{personality_data.description}"
        else:
            response = """type /sad, /business_bro or /creepy"""
        
        self.bot.reply_to(message, response)
    
    def handle_message(self, message):
        if message.text:
            user_id = message.from_user.id
            response = self.generate_chat_response(user_id, message.text)
            self.bot.send_message(message.chat.id, response)
        else:
            self.bot.reply_to(message, "Please send text only.")
    
    def setup_handlers(self):
        self.bot.message_handler(commands=['business_bro', 'sad', 'creepy', 'start', 'settings'])(
            self.handle_personality_command
        )
        self.bot.message_handler(func=lambda message: True)(
            self.handle_message
        )
    
    def run(self):
        print("Bot is running...")
        # if self.user_id:  
        #     self.bot.send_message(self.user_id, text='Bot is up and running!') #erste message in telegram settings speichern
        self.bot.infinity_polling()

if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()