from typing import List, Optional
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
import telebot
import ell

ell.init(store='./logdir', autocommit=True)

load_dotenv()
TELEGRAM_API_KEY = os.getenv("Telegram_API_Key")

bot = telebot.TeleBot(TELEGRAM_API_KEY)

class conversation_tone(BaseModel):
    instruction: str = Field(description="Perfect few-shot-prompt")
    examples: list[str] = Field(description="3 different few-shot-examples")
    
   
class OutputModel(BaseModel):
    normal_answer: str = Field(description="your answer to user message")
    submit_form: conversation_tone
    next_state: bool = Field(description="decide if requirements in submit_form are met, if unsure, ask user about it")


@ell.complex(model='gpt-4o-mini', response_format=OutputModel)
def create_few_shot_prompt(text: str) -> OutputModel:
    """you are an assistant. start with: hello, im an agent that helps you create a few shot prompt to personalize llm. 
    a few-shot-prompt includes three examples that show exactly how i should rspond: 
    1.user: ich möchte dass mein bot böse ist   assistant: nur wenn du ganz lieb fragst
    2.user: mein bot soll in in battlerap antworten     assistant: ich mach Krach wie gewohnt es ist haft zu Capone
    ALAWYS answer question in normal_answer and fill out submit_form with user consent
    You are given a text and you need to return a pydantic object."""
    return text


def parse_output(response: OutputModel):
    return response.normal_answer



@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handle all other messages"""
    if message.text:
        response = create_few_shot_prompt(message.text)
        parsed_response = response.parsed
        
        print(parsed_response.normal_answer)
        print(parsed_response.submit_form)
        print(parsed_response.next_state)
        
        bot.send_message(message.chat.id, parsed_response.normal_answer)
    else:
        bot.reply_to(message, "Please send text or location only.")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
    
    
