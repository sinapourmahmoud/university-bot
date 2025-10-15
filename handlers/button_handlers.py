from utils.locations import locations
from telebot.types import InlineKeyboardButton,InlineKeyboardMarkup
def button_handlers(bot):
    @bot.message_handler(func=lambda msg:True)
    def buttons(message):
        match(message.text):
            case'📍 مکان‌ها':
                find_locations(message)
            case 'لیست دروس 📚':
                lessons_list(message)
            case '🔗 لینک‌ها':
                links(message)
            case 'شماره‌ها 📞':
                send_numbers(message)
    
    
    def links(message):
       text = (
        "🔗 <b>لینک‌های مفید</b>\n\n"
        "➖ <a href='https://t.me/tabrizcs'>اخبار گروه علوم کامپیوتر</a>\n"
        "➖ <a href='https://t.me/anjomancs'>انجمن علمی گروه علوم کامپیوتر</a>\n"
        "➖ <a href='https://t.me/CS404_TBZ'>از من بپرس</a>\n"
        "➖ <a href='https://t.me/riazitabriz967'>دانشکده علوم ریاضی</a>\n"
        "➖ <a href='https://t.me/mathTabrizu'>اطلاعیه‌های دانشکده ریاضی، آمار و علوم کامپیوتر</a>\n"
        "➖ <a href='https://t.me/publictabrizuniversity'>کانال دانشگاه تبریز</a>\n"
        "➖ <a href='https://t.me/shourasenfi_tabrizu'>شورای صنفی-رفاهی</a>\n"
        "➖ <a href='https://t.me/Tabriz_university_students'>اجتماع دانشجویان دانشگاه تبریز</a>\n"
        "➖ <a href='https://t.me/TabrizU_Kalagh'>کلاغ دانشگاه تبریز</a>\n"
        "➖ <a href='https://t.me/sedayedaneshjoyan'>صدای دانشجویان دانشگاه تبریز</a>\n"
        "➖ <a href='https://samad.tabrizu.ac.ir/'>سایت سماد دانشگاه تبریز (امور دانشجویی)</a>\n"
        "➖ <a href='https://amozesh.tabrizu.ac.ir/'>سایت سما دانشگاه تبریز (امور آموزشی)</a>\n"
        "➖ <a href='https://refah.swf.ir/'>سایت صندوق رفاه دانشجویان</a>\n"
        "➖ <a href='https://tabrizu.ac.ir/fa'>سایت دانشگاه تبریز</a>"
        )
       
       bot.send_message(message.chat.id, text, parse_mode="HTML", disable_web_page_preview=True)
    
    
    def find_locations(message):
        
        for location in locations:
            bot.send_message(message.chat.id,location['title'])
            bot.send_location(message.chat.id, latitude=location['latitude'], longitude=location['longitude'])
        
    def send_numbers(message):
        bot.send_message(message.chat.id,"""📞 شماره‌ها

➖ کارشناس گروه علوم کامپیوتر (آقای شریفی):
+984133344015

➖ آموزش علوم کامپیوتر (خانم مرندی):
+984133392844

➖ تلفن گویا دانشکده ریاضی:
+984133392869""")
        
        
    def lessons_list(message):
        with open('./utils/documents/chart.pdf','rb') as doc:
            bot.send_document(message.chat.id,doc,caption='برنامه_8_ترمی_رشته_علوم_کامپيوترورودی_97_به_بعد')
        with open('./utils/documents/lessons.pdf','rb') as doc:
            bot.send_document(message.chat.id,doc,caption='برنامه_دروس_مقطع_کارشناسی_رشته_علوم_کامپيوتر')
            
            
            
                