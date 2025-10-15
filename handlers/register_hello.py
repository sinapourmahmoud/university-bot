from pprint import pprint
from telebot.types import ReplyKeyboardMarkup
def register_hello(bot):
    
    wraper=ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard=False)
    wraper.add('📍 مکان‌ها','لیست دروس 📚','🔗 لینک‌ها','شماره‌ها 📞')
    
    @bot.message_handler(commands=['start'])
    def hello(message):
        name=message.from_user.first_name
        bot.send_message(message.chat.id,f"""
                         
                         سلام {name} 👋
به ربات علوم کامپیوتر دانشگاه تبریز خوش اومدی.

👾 من یه ربات کمکی برای دانشجوهای رشته‌ی علوم کامپیوتر دانشگاه تبریزم.

اگه یه سر اومدی دانشگاه ولی نمی‌دونستی جایی که می‌خوای رو چطوری پیدا کنی، دکمه‌ی «📍 مکان‌ها» رو بزن.

یا اگه می‌خواستی بدونی چه درس‌هایی رو باید پاس کنی دکمه‌ی «لیست دروس 📚» رو بزن.

لینک‌های مورد نیاز و شماره‌های مورد نیاز هم توی بخش «🔗 لینک‌ها» و «شماره‌ها 📞» هستن.

می‌تونی چیزی که می‌خوای رو از منوی پایین پیدا کنی ☺️
                         """,reply_markup=wraper)