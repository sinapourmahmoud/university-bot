from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.locations import locations

def register_buttons(bot):

    @bot.message_handler(func=lambda msg: True)
    def buttons(message):
        match message.text:
            case '📍 مکان‌ها':
                send_location_menu(message)
            case 'لیست دروس 📚':
                send_lessons(message)
            case '🔗 لینک‌ها':
                send_links(message)
            case 'شماره‌ها 📞':
                send_numbers(message)


    def send_location_menu(message):
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🛟 مکان‌های رفاهی و تفریحی", callback_data='facilities'),
            InlineKeyboardButton("🏢 خوابگاه‌ها", callback_data='dormitories'),
            InlineKeyboardButton("🍕 رستوران‌ها", callback_data='restaurants'),
            InlineKeyboardButton("📕 مکان‌های علمی و آموزشی", callback_data='educations')
        )
        bot.send_message(message.chat.id, "📍 لطفاً دسته‌بندی مورد نظر رو انتخاب کن:", reply_markup=markup)


    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):
        print(f"CALLBACK RECEIVED: {call.data}")  

        if call.data == 'facilities':
            send_locations(call.message, locations['facilities'], "🛟 مکان‌های رفاهی و تفریحی")
        elif call.data == 'dormitories':
            send_locations(call.message, locations['dormitories'], "🏢 خوابگاه‌ها")
        elif call.data == 'restaurants':
            send_locations(call.message, locations['restaurants'], "🍕 رستوران‌ها")
        elif call.data == 'educations':
            send_locations(call.message, locations['educations'], "📕 مکان‌های علمی و آموزشی")

    def send_locations(message, location_list, title):
        bot.send_message(message.chat.id, f"📍 {title}:")
        for loc in location_list:
            bot.send_message(message.chat.id, f"📍 {loc['title']}")
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
        text = """def links(message):
    text = 
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
