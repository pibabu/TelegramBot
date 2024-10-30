import telebot

bot = telebot.TeleBot("xxx", parse_mode=None) # You can set parse_mode by default. HTML or MARKDOWN

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Howdy, how are you doing?")
 
@bot.message_handler(commands=["hello"])
def say_hello(message):
    bot.reply_to(message, "Hey, hier kannst du personalisiern, wähle /hello/one oder was")
    
@bot.message_handler(commands=["hello/one"])
def say_heyho(message):
    bot.reply_to(message, "heyho")

    

@bot.message_handler(func=lambda message: True)
def echo_all(message):
	bot.reply_to(message, message.text)

bot.infinity_polling()