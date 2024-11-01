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

# class conversation_tone(BaseModel):
#     #instruction: str = Field(description="Perfect few-shot-prompt")
#     examples: list[str] = Field(description="3 creative few-shot-examples")
    
   
class OutputModel(BaseModel):
    assistant_answer: str = Field(description="your coordination channel to help user create perfect few-shot-prompt")
    example_questions: list[str] = Field(description="""three q and a examples with surprisingly creative llm answers. ONLY
                                         fill if user is positive""")
    next_state: bool = Field(description="""decide if requirements are met (do we have perfect few-shot-prompt?)
                             if unsure, ask user""")


@ell.complex(model='gpt-4o-mini', response_format=OutputModel)
def create_few_shot_prompt(text: str) -> OutputModel:
    """your job: assist in creating 3 few-shot-examples, you communicate with user via: assistant_answer
    examples: 
    user: talk in business bro, sell the shit out of it  ai: We ll turn this into a powerhouse of disruptive, high-touch, 
    value-packed synergy thatll resonate with every stakeholder in the room bro
    
    user: you are a sad bot.how was your day?    ai: You wake up each day not out of choice, but because your body simply does. 
    Life doesnt feel chosen; its more like an awkward habit you havent yet dropped
    
    user: you are a bit creepy  ai: Found myself parked in a shadowy alley, watching a nondescript building. 
    Time crawled, each tick amplifying the tension between you and me: i am watching YOU"""
    return text


# def parse_output(response: OutputModel):
#     return response.normal_answer, response.example_questions

def parse_output(response: OutputModel):
    combined_output = f"{response.assistant_answer} {response.example_questions}"
    return combined_output

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handle all other messages"""
    if message.text:
        response = create_few_shot_prompt(message.text)
        parsed_response = response.parsed
        combined_output = parse_output(parsed_response)
        
        # print(parsed_response.normal_answer)
        # print(parsed_response.combined_output)
        # print(parsed_response.next_state)
        
        bot.send_message(message.chat.id, combined_output)
    else:
        bot.reply_to(message, "Please send text or location only.")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
    
    
