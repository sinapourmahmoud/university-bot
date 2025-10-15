def button_handlers(bot):
    @bot.message_handler(func=lambda msg:True)
    def buttons(message):
        match(message.text):
            case'📍 مکان‌ها':
                print('kasakam')
            case 'لیست دروس 📚':
                bot.send_message(message.chat.id,'dars ha')
            case '🔗 لینک‌ها':
                links(message)
            case 'شماره‌ها 📞':
                bot.send_message(message.chat.id,'phones')
    
    
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

        
                