import telebot
from pprint import pprint
from telebot.types import InlineKeyboardButton,InlineKeyboardMarkup
bot=telebot.TeleBot('7957636569:AAHjRB7tvPXCtSING70W6FlGyz75HTp0trk')

button1=InlineKeyboardButton(text="Button1",callback_data='btn1')
button2=InlineKeyboardButton(text="Button2",callback_data='btn2')

wraper=InlineKeyboardMarkup(row_width=1)
wraper.add(button1,button2)


@bot.message_handler(commands=['start'])
def write_wellcome(message):
    # this is for sending message
    bot.send_message(message.chat.id,'welcome baby\nplease enter your name:',reply_markup=wraper)
    
    # this is for reply
    # bot.reply_to(message,"reply")
#     bot.register_next_step_handler(message,ask_name)

# def ask_name(message):
#     name=message.text
#     bot.send_message(message.chat.id,f" your name is {name}")



@bot.callback_query_handler(lambda call:True)
def check_button(call):
    if(call.data=='btn1'):
        bot.answer_callback_query(call.id,'btn1 is pressed',show_alert="it is pressed")


bot.polling()