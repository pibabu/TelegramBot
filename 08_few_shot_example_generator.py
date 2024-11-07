from typing import List
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
import telebot
import ell

ell.init(store="./logdir", autocommit=True, verbose=True)
load_dotenv()
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
bot = telebot.TeleBot(TELEGRAM_API_KEY)


class OutputModel(BaseModel):
    assistant_answer: str = Field(
        description="Channel for coordinating with user about example creation and receiving feedback"
    )
    example_questions: List[str] = Field(
        description="Three Q&A examples demonstrating the chosen personality style"
    )
    keep_state: bool = Field(
        description="Set to False ONLY if user explicitly APPROVES examples"
    )


@ell.complex(model="gpt-4o-mini", response_format=OutputModel)  ####add chat hirstory
def create_few_shot_prompt(text: str):
    """Your job: Help users create and refine 3 few-shot examples for their chosen personality style.

    Process:
    1. If no personality specified yet: Ask user to describe desired personality/style
    2. If personality specified: Generate 3 example Q&A pairs in that style
    3. Keep iterating based on user feedback until they're satisfied

    Key points:
    - Each example should clearly demonstrate the chosen personality
    - Examples should be diverse but consistent in style
    - Pay attention to user feedback and adjust accordingly
    - Only set <keep_state>=False when user explicitly approves examples

    Example interaction flow:

    user: "I want a motivational gym bro personality"
    assistant_answer: "I'll create 3 examples of a motivational gym bro style! Check these out and let me know if they need tweaking 💪"
    example_questions: [
        "Q: How's my progress?\nA: LETS GOOO KING! Every rep is building your legacy! You're not just lifting weights, you're lifting your LIMITS! 🔥",
        "Q: Should I skip today?\nA: ABSOLUTELY NOT Bro! Winners were made on the days they didn't feel like it! Time to CRUSH IT! 💪",
        "Q: What's your secret?\nA: THE GRIND NEVER STOPS BRO! Eat clean, train mean, and stay HUNGRY for gains! We're all gonna make it! 🏋️‍♂️"
    ]
    keep_state: true

    user: "make it less aggressive but keep the energy"
    assistant_answer: "Got it! I'll dial back the intensity while maintaining the positive energy. How about these?"
    example_questions: [
        "Q: How's my progress?\nA: You're absolutely crushing it, friend! Every step forward is a win - and you're stacking wins like a champion! 🌟",
        "Q: Should I skip today?\nA: Listen champ, your future self will thank you for showing up today. Let's make this workout count! 💪",
        "Q: What's your secret?\nA: Consistency is your superpower! Stay positive, keep showing up, and watch yourself transform! You've got this! ✨"
    ]
    keep_state: true

    user: "perfect!lets keep them"
    assistant_answer: "alrighty, i save these exapmes. see you later"
    example_questions: [previous examples repeated]
    keep_state: false
    """
    return text


def parse_output(response: OutputModel) -> str:
    examples = "\n\n".join(response.example_questions)
    return f"{response.assistant_answer}\n\n{examples}"


@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text:
        response = create_few_shot_prompt(message.text)
        combined_output = parse_output(response.parsed)
        parsed_response = response.parsed
        print(f"weiter in example generator bleiben:{parsed_response.keep_state}")

        bot.send_message(message.chat.id, combined_output)
    else:
        bot.reply_to(message, "Please send text only.")


if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
