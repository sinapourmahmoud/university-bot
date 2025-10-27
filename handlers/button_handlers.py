from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.locations import locations
from utils.socialmedia import socialmedias
import sqlite3

DB_PATH='cinema.db'



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
            case '🌐 مجازی':
                social_medias(message)
            case '🍏 درباره ما 🚬':
                about_us(message)
            case 'بریم سینما 🎬':
                cinema_menu(message.chat.id)


    def send_location_menu(chat_id):
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🛟 مکان‌های رفاهی و تفریحی", callback_data='cat-facilities'),
            InlineKeyboardButton("🏛 خوابگاه‌ها", callback_data='cat-dormitories'),
            InlineKeyboardButton("🌭 سلف‌ها", callback_data='cat-restaurants'),
            InlineKeyboardButton("🌭 رستوران‌ها(تاک‌ها)", callback_data='cat-free_restaurants'),
            InlineKeyboardButton("📖 مکان‌‌های علمی و آموزشی", callback_data='cat-educations')
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
        



    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):
        print(f"CALLBACK RECEIVED: {call.data}")  

        if 'cat-' in call.data:
            location_sub_menu(call.message,call.data)
        
        elif 'part-' in call.data:
            send_locations(call.message,call.data)
        
        elif call.data=='back_main':
            edit_to_main(call.message)
        elif call.data=='student':
            student_signup(call.message)
        elif call.data=='foreign':
            foreign_signup(call.message)
            
        

    def student_signup(message):

        
        
        bot.send_message(message.chat.id, "✍️ لطفا نام خود را وارد نمایید")
        bot.send_message(message.chat.id, 'برای خروج exit وارد کنید')
        bot.register_next_step_handler(message, save_name)
    
    
    def foreign_signup(message):
        
        
        
        bot.send_message(message.chat.id, "✍️ لطفا نام خود را وارد نمایید")
        bot.send_message(message.chat.id, 'برای خروج exit وارد کنید')
        bot.register_next_step_handler(message, save_foreign_name)
        
    def save_foreign_name(message):
        full_name=message.text.strip()
        if full_name=='exit':
            
            cinema_menu(message.chat.id)
            return
        tg_id=int(message.from_user.id)
        
        conn=sqlite3.connect(DB_PATH)
        cursor=conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (tg_id, full_name, status,is_student)
            VALUES (?, ?, 'collecting',0)
            ON CONFLICT(tg_id) DO UPDATE SET full_name=excluded.full_name, status='collecting'
        """,(tg_id,full_name))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "🎓 شماره دانشجویی معرف خود را وارد نمایید:")
        bot.register_next_step_handler(message, friend_id_handler)
        
        
    def friend_id_handler(message):
        tg_id = int(message.from_user.id)
        friend_id_text = message.text.strip()
        if friend_id_text=='exit':
            cinema_menu(message.chat.id)
            return
        if not friend_id_text.isdigit():
            bot.send_message(message.chat.id, "❌ فقط عدد قابل قبول است:")
            return bot.register_next_step_handler(message, friend_id_handler)
        friend_id = int(friend_id_text)
        
        print(friend_id)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT is_student FROM users WHERE student_id_card=?",(friend_id,))
        row = cur.fetchone()
        
        conn.close()

        if not row:
            bot.send_message(message.chat.id,
                            "❌ چنین کاربری در سیستم موجود نمیباشد.دوباره امتحان کنید:")
            return bot.register_next_step_handler(message, friend_id_handler)

        if row[0] != 1:  # not a student
            bot.send_message(message.chat.id,
                            "❌ چنین کاربری به عنوان دانشجو ثبت نشده است.لطفا دوباره امتحان کنید:")
            return bot.register_next_step_handler(message, friend_id_handler)

        # 3) If valid → save for guest
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            UPDATE users
            SET is_student=0, linked_student_id=?, status='collecting'
            WHERE tg_id=?
        """, (friend_id, tg_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "📸 تصویر فیش واریزی را ارسال نمایید:")
        bot.register_next_step_handler(message, guest_payment_proof)
    
    
    
    def guest_payment_proof(message):
        if message.text:
            if message.text=='exit':
                cinema_menu(message.chat.id)
                return
        tg_id = int(message.from_user.id)
        
        if not message.photo:
            bot.send_message(message.chat.id, "❌ لطفا عکس بفرستید.")
            return bot.register_next_step_handler(message, guest_payment_proof)

        # 2) Get highest resolution photo file_id
        file_id = message.photo[-1].file_id

        # 3) Save in DB
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            UPDATE users
            SET payment_proof_file_id=?, status='waiting_admin'
            WHERE tg_id=?
        """, (file_id, tg_id))
        conn.commit()
        conn.close()

        # 4) Inform user
        bot.send_message(message.chat.id, "✅ فیش دریافت شد. لظفا منتظر تایید ادمین باشید")
    
    
    def save_name(message):
        full_name=message.text.strip()
        if full_name=='exit':
            cinema_menu(message.chat.id)
            return
        tg_id=int(message.from_user.id)
        
        conn=sqlite3.connect(DB_PATH)
        cursor=conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (tg_id, full_name, status,is_student)
            VALUES (?, ?, 'collecting',1)
            ON CONFLICT(tg_id) DO UPDATE SET full_name=excluded.full_name, status='collecting'
        """, (tg_id, full_name))
        conn.commit()
        conn.close()

        bot.send_message(message.chat.id, "🎓 شماره دانشجویی خود را وارد نمایید:")
        bot.register_next_step_handler(message, save_id_card)
       
    
    
    def save_id_card(message):
        
        student_id=message.text.strip()
        tg_id=int(message.from_user.id)
        if student_id=='exit':
            cinema_menu(message.chat.id)
            return
        if not student_id.isdigit():
            bot.register_next_step_handler(message, save_id_card)
            
            return
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            UPDATE users SET is_student=1, student_id_card=?, status='collecting'
            WHERE tg_id=?
        """, (int(student_id), tg_id))
        conn.commit()
        conn.close()

        bot.send_message(message.chat.id, "📸 تصویر فیش واریزی را ارسال نمایید:")
        bot.register_next_step_handler(message, wait_for_payment_photo)
        

    def wait_for_payment_photo(message):
        
        if message.text:
            if message.text=='exit':
                cinema_menu(message.chat.id)
                return
        if not message.photo:
            bot.send_message(message.chat.id, "❌ لطفا عکس بفرستید.")
            bot.register_next_step_handler(message, wait_for_payment_photo)
            return
        
        file_id = message.photo[-1].file_id
        tg_id = int(message.from_user.id)

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            UPDATE users
            SET payment_proof_file_id=?, status='waiting_admin'
            WHERE tg_id=?
        """, (file_id, tg_id))
        conn.commit()
        conn.close()

        bot.send_message(message.chat.id, "✅ فیش دریافت شد. لظفا منتظر تایید ادمین باشید")
    
    
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
        print(message.from_user.id)
        text = """
        🔗 لینک‌های مفید\n\n
        ➖ اخبار گروه علوم کامپیوتر:\nhttps://t.me/tabrizcs\n
        ➖ از من بپرس:\nhttps://t.me/CS404_TBZ\n
        ➖ دانشکده علوم ریاضی:\nhttps://t.me/riazitabriz967\n
        ➖ اطلاعیه‌های دانشکده ریاضی، آمار و علوم کامپیوتر:\nhttps://t.me/mathTabrizu\n
        ➖ کانال دانشگاه تبریز:\nhttps://t.me/publictabrizuniversity\n
        ➖ سایت سماد دانشگاه تبریز (امور دانشجویی):\nhttps://samad.tabrizu.ac.ir/\n
        ➖ سایت سما دانشگاه تبریز (امور آموزشی):\nhttps://amozesh.tabrizu.ac.ir/\n
        ➖ شورای صنفی-رفاهی:\nhttps://t.me/shourasenfi_tabrizu\n
        ➖ اجتماع دانشجویان دانشگاه تبریز:\nhttps://t.me/Tabriz_university_students\n
        ➖ کلاغ دانشگاه تبریز:\nhttps://t.me/TabrizU_Kalagh\n
        ➖ صدای دانشجویان دانشگاه تبریز:\nhttps://t.me/sedayedaneshjoyan\n
        ➖ سایت صندوق رفاه دانشجویان:\nhttps://refah.swf.ir/\n
        ➖ سایت دانشگاه تبریز:\nhttps://tabrizu.ac.ir/fa
    

"""
        bot.send_message(message.chat.id, text, disable_web_page_preview=True)
    
    def social_medias(message):
        markup=InlineKeyboardMarkup(row_width=1)
        for media in socialmedias:
            markup.add(InlineKeyboardButton(text=media['title'],callback_data=media['data'],url=media['link']))
        bot.send_message(message.chat.id,text='مارا در صفحات مجازی دنبال کنید',reply_markup=markup)
    
    def about_us(message):
        text = """🎓 انجمن علمی دانشجویی علوم کامپیوتر دانشگاه تبریز

ما یه جمع خودمونی از دانشجوهای علاقه‌مند به دنیای کامپیوتر و فناوری‌ایم 💻✨

اینجا توی انجمن علمی علوم کامپیوتر دانشگاه تبریز، دور هم جمع شدیم تا یاد بگیریم، یاد بدیم و با هم رشد کنیم 🚀

هدفمون ایجاد یه فضای پویاست برای یادگیری، اشتراک تجربه، برگزاری کارگاه‌ها، مسابقات، و کلی فعالیت خفن علمی و فرهنگی 📓

🔹 اعضای انجمن:

1️⃣ ساناز سلیمانی
2️⃣ سینا پورمحمود
3️⃣ کیمیا میره‌کی
4️⃣ محمدحسین رضازاده
5️⃣ سروین حسینی
6️⃣ پرنیان حبیبی
7️⃣ فائزه موسی‌پور
8️⃣ آرسام ذالی
9️⃣ ائلیار آزادوار

🔺تشکر ویژه از:

➖ حسین حبیبی 
بابت ایده ربات
➖ بهزاد پورمحمود
بابت تمامی حمایت‌های مادی و معنوی

🎁 راستی چون همه دانشجوی کامپیوتر هستیم، گفتیم که بد نیست پروژه رو به صورت متن‌باز قرار بدیم. اگه خواستید، می‌تونید یه سر به [مخزن پروژه](https://github.com/sinapourmahmoud/university-bot/tree/main) بزنید و ⭐️ یادتون نره!

📍 انجمن علمی علوم کامپیوتر دانشگاه تبریز — جایی برای ایده‌ها، خلاقیت و دوستی 🤍
"""
        bot.send_message(message.chat.id, text, parse_mode="Markdown")


    def cinema_menu(chat_id):
        
        
        with open('./utils/documents/poster.jpg','rb') as photo:
            bot.send_photo(chat_id, photo, caption="""💳 هزینه شرکت در برنامه سینما:
🧑🏻‍🎓برای دانشجوهای دانشکده‌مون: ۸۵٬۰۰۰ تومان
🙋🏻 برای مهمان‌های خارج دانشکده: ۹۵٬۰۰۰ تومان
📌 نکته مهم:
مهمان‌های خارج از دانشکده برای ثبت‌نام نیاز به معرف از داخل دانشکده دارن. (یعنی یکی از بچه‌های دانشکده اول باید ثبت‌نام کنه و بعد بتونه معرف دوستش بشه).
🎞️ فیلم و زمان هر برنامه قبل از اجرا اعلام میشه، پس چشم از چنل CS PLUS برندار ;)""")
        
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("۸۵,۰۰۰ تومان", callback_data='student'),
            InlineKeyboardButton("۹۵,۰۰۰ تومان", callback_data='foreign'),
            
        )
        bot.send_message(chat_id, "لطفا مبلغ مورد نظر را انتخاب کتید", reply_markup=markup)
        
    

