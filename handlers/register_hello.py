from telebot.types import ReplyKeyboardMarkup,InlineKeyboardButton, InlineKeyboardMarkup
from utils.code_generator import generate_unique_code
from db import User,session

DB_PATH='/data/cinema.db'

ADMIN_IDS=[108738885,428097665]



def register_hello(bot):
    
    wraper=ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard=False)
    wraper.add('📍 مکان‌ها','لیست دروس 📚','🔗 لینک‌ها','شماره‌ها 📞','🌐 مجازی','🍏 درباره ما 🚬','🍉 یلدا سی‌اس 🍉')
    
    @bot.message_handler(commands=['start'])
    def hello(message):
        tg_id = str(message.from_user.id)
        user = session.query(User).filter_by(tg_id=tg_id).first()
    
        if user and user.status == 'collecting':
            bot.send_message(message.chat.id, "⛔ شما در جریان ثبت‌نام سینما هستید. ابتدا exit را بزنید.")
            return
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
        
        
    def handle_database_pending():
        rows = session.query(
            User.tg_id,
            User.full_name,
            User.is_student,
            User.linked_student_id,
            User.payment_proof_file_id,
            User.status,
            User.ticket_code
        ).filter_by(status='waiting_admin').all()

        # rows is now a list of tuples like [(tg_id, full_name, ...), ...]
        return rows


    def update_database(tg_id,status):
        user = session.query(User).filter_by(tg_id=tg_id).first()

        if user:
            user.status = status
            session.commit()
        else:
            # Optional: handle missing user
            user = User(tg_id=tg_id, status=status)
            session.add(user)
            session.commit()


    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if message.from_user.id not in ADMIN_IDS:
            bot.reply_to(message, "❌ You are not authorized.")
            return 
        pending = handle_database_pending()
        if not pending:
            bot.send_message(message.chat.id, "✅ No pending payments.")
        bot.send_message(message.chat.id,f"{pending}")
    
    
        for (tg_id,full_name,is_student,linked_student_id,payment_proof_file_id,status,ticket_code) in pending:
            markup=InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{tg_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject:{tg_id}")
            )
            bot.send_photo(message.chat.id, payment_proof_file_id, caption=f"User: {full_name}\nTelegram ID: {tg_id}", reply_markup=markup)
            
            
    @bot.callback_query_handler(func=lambda c: c.data.startswith(("approve", "reject")))
    def callback_query(call):
        action, tg_id = call.data.split(":")


        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "❌ Not authorized")
            return

        if action == "approve":
            update_database(tg_id, "approved")
            code = generate_unique_code()

            # Get user from DB
            user = session.query(User).filter_by(tg_id=tg_id).first()
            if user:
                user.ticket_code = code
                session.commit()
                bot.send_message(
                    tg_id,
                    f"✅ پرداخت با موفقیت صورت گرفت. کد قرعه کشی شما: [{code}]"
                )
                bot.send_location(tg_id, latitude=38.0752305, longitude=46.2870694)
                bot.send_message(tg_id,"سینما ۲۹ بهمن تبریز")

            bot.answer_callback_query(call.id, "Approved ✅")

        elif action == "reject":
            update_database(tg_id, "rejected")
            bot.send_message(
                tg_id,
                "❌ پرداخت شما رد شد. لطفا با ادمین در ارتباط باشید"
            )
            bot.answer_callback_query(call.id, "Rejected ❌")



