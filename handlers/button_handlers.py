from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.locations import locations

def register_buttons(bot):

    @bot.message_handler(func=lambda msg: True)
    def buttons(message):
        match message.text:
            case '📍 مکان‌ها':
                send_location_menu(message.chat.id)
            case 'لیست دروس 📚':
                send_lessons(message)
            case '🔗 لینک‌ها':
                send_links(message)
            case 'شماره‌ها 📞':
                send_numbers(message)


    def send_location_menu(chat_id):
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🛟 مکان‌های رفاهی و تفریحی", callback_data='cat-facilities'),
            InlineKeyboardButton("🏛 خوابگاه‌ها", callback_data='cat-dormitories'),
            InlineKeyboardButton("🌭 سلف ها", callback_data='cat-restaurants'),
            InlineKeyboardButton("🌭 رستوران ها(تاک ها)", callback_data='cat-free_restaurants'),
            InlineKeyboardButton("📖 مکان‌های علمی و آموزشی", callback_data='cat-educations')
        )
        bot.send_message(chat_id, "📍 لطفاً دسته‌بندی مورد نظر رو انتخاب کن:", reply_markup=markup)

    def edit_to_main(call):
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🛟 مکان‌های رفاهی و تفریحی", callback_data='cat-facilities'),
            InlineKeyboardButton("🏛 خوابگاه‌ها", callback_data='cat-dormitories'),
            InlineKeyboardButton("🌭 سلف ها", callback_data='cat-restaurants'),
            InlineKeyboardButton("🌭 رستوران ها(تاک ها)", callback_data='cat-free_restaurants'),
            InlineKeyboardButton("📖 مکان‌های علمی و آموزشی", callback_data='cat-educations')
        )
        bot.edit_message_text(
            chat_id=call.chat.id,
            message_id=call.message_id,
            text="📍 لطفاً دسته‌بندی مورد نظر را انتخاب کنید:",
            reply_markup=markup,
        )

    def location_sub_menu(call,category):
        markup=InlineKeyboardMarkup(row_width=1)
        
        for loc in locations[category]:
            markup.add(
            InlineKeyboardButton(loc['title'],callback_data=loc['data'])
            )
        markup.add(InlineKeyboardButton("🔙 بازگشت",callback_data='back_main'))
        
        bot.edit_message_text(chat_id=call.chat.id,message_id=call.message_id,text=f"📍 یکی را انتخاب کنید:",reply_markup=markup)
        

    def location_details(call,data):
        for cat in locations:
            for loc in cat:
                if loc['data']==data:
                    bot.send_location(call.chat.id,latitude=loc['latitude'], longitude=loc['longitude'])

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):
        print(f"CALLBACK RECEIVED: {call.data}")  

        if 'cat-' in call.data:
            location_sub_menu(call.message,call.data)
        
        elif 'part-' in call.data:
            send_locations(call.message,call.data)
        
        elif call.data=='back_main':
            edit_to_main(call.message)
        



    def send_locations(message, data):
        for cat in  locations.items():
            for loc in cat[1]:
                if loc['data']==data:
                    bot.send_message(message.chat.id, f"📍 {loc['title']}:")

                    bot.send_location(message.chat.id, latitude=loc['latitude'], longitude=loc['longitude'])
        
    def send_numbers(message):
        bot.send_message(message.chat.id, """📞 شماره‌ها

➖ کارشناس گروه علوم کامپیوتر (آقای شریفی):
+984133344015

➖ آموزش علوم کامپیوتر (خانم مرندی):
+984133392844

➖ تلفن گویا دانشکده ریاضی:
+984133392869""")

    def send_lessons(message):
        with open('./utils/documents/chart.pdf', 'rb') as doc:
            bot.send_document(message.chat.id, doc, caption='برنامه ۸ ترمی رشته علوم کامپیوتر')
        with open('./utils/documents/lessons.pdf', 'rb') as doc:
            bot.send_document(message.chat.id, doc, caption='لیست دروس رشته علوم کامپیوتر')

    def send_links(message):
        text = """
        🔗 لینک‌های مفید\n\n
        ➖ اخبار گروه علوم کامپیوتر:\nhttps://t.me/tabrizcs\n
        ➖ انجمن علمی گروه علوم کامپیوتر:\nhttps://t.me/anjomancs\n
        ➖ از من بپرس:\nhttps://t.me/CS404_TBZ\n
        ➖ دانشکده علوم ریاضی:\nhttps://t.me/riazitabriz967\n
        ➖ اطلاعیه‌های دانشکده ریاضی، آمار و علوم کامپیوتر:\nhttps://t.me/mathTabrizu\n
        ➖ کانال دانشگاه تبریز:\nhttps://t.me/publictabrizuniversity\n
        ➖ شورای صنفی-رفاهی:\nhttps://t.me/shourasenfi_tabrizu\n
        ➖ اجتماع دانشجویان دانشگاه تبریز:\nhttps://t.me/Tabriz_university_students\n
        ➖ کلاغ دانشگاه تبریز:\nhttps://t.me/TabrizU_Kalagh\n
        ➖ صدای دانشجویان دانشگاه تبریز:\nhttps://t.me/sedayedaneshjoyan\n
        ➖ سایت سماد دانشگاه تبریز (امور دانشجویی):\nhttps://samad.tabrizu.ac.ir/\n
        ➖ سایت سما دانشگاه تبریز (امور آموزشی):\nhttps://amozesh.tabrizu.ac.ir/\n
        ➖ سایت صندوق رفاه دانشجویان:\nhttps://refah.swf.ir/\n
        ➖ سایت دانشگاه تبریز:\nhttps://tabrizu.ac.ir/fa
    

"""
        bot.send_message(message.chat.id, text, disable_web_page_preview=True)



