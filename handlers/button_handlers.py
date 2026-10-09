import logging
from pathlib import Path

from requests.exceptions import RequestException
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from db import Event, Registration, SessionLocal, User
from handlers.cinema_registration import (
    begin_registration as begin_cinema_registration,
)
from utils.locations import locations
from utils.socialmedia import socialmedias


BASE_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = BASE_DIR / "utils" / "documents"
logger = logging.getLogger(__name__)


def register_buttons(bot):

    @bot.message_handler(func=lambda msg: True)
    def buttons(message):
        text = (message.text or "").strip()

        if text == "📍 مکان‌ها":
            send_location_menu(message.chat.id)

        elif text == "لیست دروس 📚":
            send_lessons(message)

        elif text == "🔗 لینک‌ها":
            send_links(message)

        elif text == "شماره‌ها 📞":
            send_numbers(message)

        elif text == "🌐 مجازی":
            social_medias(message)

        elif text == "🍏 درباره ما 🚬":
            about_us(message)

        elif text in ("🎬 برنامه‌ها", "🎬 سینما"):
            send_events_menu(message)

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("cat-")
        or call.data.startswith("part-")
        or call.data in {
        "back_locations",
        "events",
        "event_cinema",
        "event_yalda",
        }
        or call.data.startswith("register:")
    )
    def handle_callback(call):
        data = call.data

        if data.startswith("event_") and data != "event_cinema":
            bot.answer_callback_query(
                call.id,
                "❌ این برنامه در حال حاضر در دسترس نیست.",
                show_alert=True,
            )
            return

        bot.answer_callback_query(call.id)

        if data.startswith("cat-"):
            location_sub_menu(call, data)
            return

        if data.startswith("part-"):
            send_location_by_data(call.message, data)
            return

        if data == "back_locations":
            edit_to_location_main(call)
            return

        if data == "events":
            send_events_menu(call.message)
            return

        if data.startswith("event_"):
            event_code = data.removeprefix("event_")
            show_event(call.message, event_code, call.from_user.id)
            return

        if data.startswith("register:"):
            parts = data.split(":")
            if len(parts) == 3 and parts[2] == "cinema":
                registration_type = parts[1]
                event_code = parts[2]
                if registration_type in {"student", "guest"}:
                    begin_event_registration(
                        call.message,
                        call.from_user.id,
                        event_code,
                        registration_type,
                    )
                    return
            bot.send_message(
                call.message.chat.id,
                "❌ درخواست ثبت‌نام نامعتبر است. لطفاً دوباره از منوی سینما اقدام کنید.",
            )

    # ---------------------------------------------------------
    # Locations
    # ---------------------------------------------------------

    def send_location_menu(chat_id):
        markup = InlineKeyboardMarkup(row_width=1)

        markup.add(
            InlineKeyboardButton(
                "🛟 مکان‌های رفاهی و تفریحی",
                callback_data="cat-facilities",
            ),
            InlineKeyboardButton(
                "🏛 خوابگاه‌ها",
                callback_data="cat-dormitories",
            ),
            InlineKeyboardButton(
                "🌭 سلف‌ها",
                callback_data="cat-restaurants",
            ),
            InlineKeyboardButton(
                "🍗 رستوران‌ها",
                callback_data="cat-free_restaurants",
            ),
            InlineKeyboardButton(
                "📖 مکان‌های علمی و آموزشی",
                callback_data="cat-educations",
            ),
        )

        bot.send_message(
            chat_id,
            "📍 لطفاً دسته‌بندی مورد نظر رو انتخاب کن:",
            reply_markup=markup,
        )

    def edit_to_location_main(call):
        markup = InlineKeyboardMarkup(row_width=1)

        markup.add(
            InlineKeyboardButton(
                "🛟 مکان‌های رفاهی و تفریحی",
                callback_data="cat-facilities",
            ),
            InlineKeyboardButton(
                "🏛 خوابگاه‌ها",
                callback_data="cat-dormitories",
            ),
            InlineKeyboardButton(
                "🌭 سلف‌ها",
                callback_data="cat-restaurants",
            ),
            InlineKeyboardButton(
                "🍗 رستوران‌ها",
                callback_data="cat-free_restaurants",
            ),
            InlineKeyboardButton(
                "📖 مکان‌های علمی و آموزشی",
                callback_data="cat-educations",
            ),
        )

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="📍 لطفاً دسته‌بندی مورد نظر را انتخاب کنید:",
            reply_markup=markup,
        )

    def location_sub_menu(call, category):
        if category not in locations:
            bot.answer_callback_query(
                call.id,
                "❌ این دسته‌بندی پیدا نشد.",
            )
            return

        markup = InlineKeyboardMarkup(row_width=1)

        for loc in locations[category]:
            markup.add(
                InlineKeyboardButton(
                    loc["title"],
                    callback_data=loc["data"],
                )
            )

        markup.add(
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="back_locations",
            )
        )

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="📍 یکی را انتخاب کنید:",
            reply_markup=markup,
        )

    def send_location_by_data(message, data):
        for category_locations in locations.values():
            for location in category_locations:
                if location["data"] == data:
                    bot.send_message(
                        message.chat.id,
                        f"📍 {location['title']}",
                    )

                    bot.send_location(
                        message.chat.id,
                        latitude=location["latitude"],
                        longitude=location["longitude"],
                    )
                    return

        bot.send_message(
            message.chat.id,
            "❌ مکان مورد نظر پیدا نشد.",
        )

    # ---------------------------------------------------------
    # Event menu
    # ---------------------------------------------------------

    def send_events_menu(message):
        with SessionLocal() as session:
            events = (
                session.query(Event)
                .filter(
                    Event.code == "cinema",
                    Event.is_active.is_(True),
                )
                .order_by(Event.id.asc())
                .all()
            )

            markup = InlineKeyboardMarkup(row_width=1)

            for event in events:
                markup.add(
                    InlineKeyboardButton(
                        event.name,
                        callback_data=f"event_{event.code}",
                    )
                )

        if not events:
            bot.send_message(
                message.chat.id,
                "⏳ ثبت‌نام سینما در حال حاضر فعال نیست.",
            )
            return

        bot.send_message(
            message.chat.id,
            "🎬 برنامه سینما:\n\nبرای دیدن جزئیات و ثبت‌نام انتخاب کنید:",
            reply_markup=markup,
        )

    def show_event(message, event_code, telegram_user_id):
        if message.chat.type != "private":
            bot.send_message(
                message.chat.id,
                "برای ثبت‌نام سینما، لطفاً از گفت‌وگوی خصوصی ربات استفاده کنید.",
            )
            return

        with SessionLocal() as session:
            event = (
                session.query(Event)
                .filter(
                    Event.code == event_code,
                    Event.is_active.is_(True),
                )
                .first()
            )

            if not event:
                bot.send_message(
                    message.chat.id,
                    "❌ این برنامه در حال حاضر فعال نیست.",
                )
                return

            tg_id = str(telegram_user_id)

            user = (
                session.query(User)
                .filter(User.tg_id == tg_id)
                .first()
            )

            registration = None

            if user:
                registration = (
                    session.query(Registration)
                    .filter(
                        Registration.user_id == user.id,
                        Registration.event_id == event.id,
                    )
                    .first()
                )

            if registration:
                if registration.status == "approved":
                    send_cinema_poster(
                        message.chat.id,
                        caption=(
                            f"✅ شما قبلاً برای «{event.name}» ثبت‌نام کرده‌اید.\n\n"
                            f"🎟 کد حضور:\n{registration.ticket_code}"
                        ),
                    )
                    return

                if registration.status == "waiting_admin":
                    send_cinema_poster(
                        message.chat.id,
                        caption=(
                            f"⏳ ثبت‌نام شما برای «{event.name}» دریافت شده "
                            "و منتظر تأیید ادمین است."
                        ),
                    )
                    return

                if registration.status == "collecting":
                    markup = InlineKeyboardMarkup(row_width=1)
                    markup.add(
                        InlineKeyboardButton(
                            "🔄 شروع دوباره ثبت‌نام",
                            callback_data=(
                                f"register:{registration.registration_type}:cinema"
                            ),
                        )
                    )
                    send_cinema_poster(
                        message.chat.id,
                        caption=(
                            "⏳ ثبت‌نام سینمای شما نیمه‌کاره مانده است. "
                            "برای شروع دوباره ادامه دهید."
                        ),
                        reply_markup=markup,
                    )
                    return

            if event.capacity is not None:
                count = (
                    session.query(Registration)
                    .filter(
                        Registration.event_id == event.id,
                        Registration.status.in_(
                            ["waiting_admin", "approved"]
                        ),
                    )
                    .count()
                )

                remaining = max(event.capacity - count, 0)

                if remaining == 0:
                    send_cinema_poster(
                        message.chat.id,
                        caption=(
                            f"⛔ ظرفیت «{event.name}» تکمیل شده است.\n\n"
                            "لطفاً برنامه‌های بعدی انجمن را دنبال کنید ❤️"
                        ),
                    )
                    return

                capacity_text = f"ظرفیت باقی‌مانده: {remaining}"
            else:
                capacity_text = "ظرفیت: آزاد"

            text = f"""
🎉 {event.name}

💰 هزینه ثبت‌نام:

🧑🏻‍🎓 دانشجویان علوم کامپیوتر:
{format_price(event.student_price)} تومان

🙋🏻 مهمان:
{format_price(event.guest_price)} تومان

📌 {capacity_text}
"""

            if event.code == "cinema":
                text += """
\nمهمان‌های خارج از دانشکده برای ثبت‌نام نیاز به معرف از داخل دانشکده دارند.
"""

            markup = InlineKeyboardMarkup(row_width=1)

            markup.add(
                InlineKeyboardButton(
                    f"{format_price(event.student_price)} تومان — دانشجوی علوم کامپیوتر",
                    callback_data=f"register:student:{event.code}",
                ),
                InlineKeyboardButton(
                    f"{format_price(event.guest_price)} تومان — مهمان",
                    callback_data=f"register:guest:{event.code}",
                ),
            )

            send_cinema_poster(
                message.chat.id,
                caption=text,
                reply_markup=markup,
            )

    def send_cinema_poster(chat_id, caption=None, reply_markup=None):
        poster_path = DOCUMENTS_DIR / "backrooms_telegram.jpg"
        if not poster_path.is_file():
            bot.send_message(
                chat_id,
                "❌ فایل پوستر سینما پیدا نشد.",
            )
            if caption:
                bot.send_message(chat_id, caption, reply_markup=reply_markup)
            return

        with poster_path.open("rb") as poster:
            try:
                bot.send_photo(
                    chat_id,
                    poster,
                    caption=caption or "🎬 پوستر فیلم",
                    reply_markup=reply_markup,
                )
            except RequestException:
                logger.exception("Could not upload the cinema poster to Telegram.")
                # Don't let a failed photo upload swallow the registration
                # buttons / status text the caller needed delivered.
                if caption:
                    bot.send_message(chat_id, caption, reply_markup=reply_markup)

    # ---------------------------------------------------------
    # Registration flow
    # ---------------------------------------------------------

    def begin_event_registration(
        message,
        telegram_user_id,
        event_code,
        registration_type,
    ):
        if event_code != "cinema":
            bot.send_message(
                message.chat.id,
                "❌ این برنامه در حال حاضر در دسترس نیست.",
            )
            return

        begin_cinema_registration(
            bot,
            message,
            telegram_user_id,
            registration_type,
        )

    # ---------------------------------------------------------
    # Static university information
    # ---------------------------------------------------------

    def send_numbers(message):
        bot.send_message(
            message.chat.id,
            """
📞 شماره‌ها

➖ کارشناس گروه علوم کامپیوتر (آقای شریفی):

+984133344015

➖ آموزش علوم کامپیوتر (خانم مرندی):

+984133392844

➖ تلفن گویا دانشکده ریاضی:

+984133392869
""",
        )

    def send_lessons(message):
        send_document(
            message,
            "chart.pdf",
            "برنامه ۸ ترمی رشته علوم کامپیوتر",
        )

        send_document(
            message,
            "lessons.pdf",
            "لیست دروس رشته علوم کامپیوتر",
        )

    def send_document(message, filename, caption):
        path = DOCUMENTS_DIR / filename

        if not path.exists():
            bot.send_message(
                message.chat.id,
                f"❌ فایل {filename} در سرور پیدا نشد.",
            )
            return

        with path.open("rb") as document:
            bot.send_document(
                message.chat.id,
                document,
                caption=caption,
            )

    def send_links(message):
        text = """
🔗 لینک‌های مفید

➖ اخبار گروه علوم کامپیوتر:
https://t.me/tabrizcs

➖ از من بپرس:
https://t.me/CS404_TBZ

➖ دانشکده علوم ریاضی:
https://t.me/riazitabriz967

➖ اطلاعیه‌های دانشکده ریاضی، آمار و علوم کامپیوتر:
https://t.me/mathTabrizu

➖ کانال دانشگاه تبریز:
https://t.me/publictabrizuniversity

➖ سایت سماد دانشگاه تبریز:
https://samad.tabrizu.ac.ir/

➖ سایت سما دانشگاه تبریز:
https://amozesh.tabrizu.ac.ir/

➖ شورای صنفی-رفاهی:
https://t.me/shourasenfi_tabrizu

➖ اجتماع دانشجویان دانشگاه تبریز:
https://t.me/Tabriz_university_students

➖ کلاغ دانشگاه تبریز:
https://t.me/TabrizU_Kalagh

➖ صدای دانشجویان دانشگاه تبریز:
https://t.me/sedayedaneshjoyan

➖ سایت صندوق رفاه دانشجویان:
https://refah.swf.ir/

➖ سایت دانشگاه تبریز:
https://tabrizu.ac.ir/fa
"""

        bot.send_message(
            message.chat.id,
            text,
            disable_web_page_preview=True,
        )

    def social_medias(message):
        markup = InlineKeyboardMarkup(row_width=1)

        for media in socialmedias:
            markup.add(
                InlineKeyboardButton(
                    text=media["title"],
                    url=media["link"],
                )
            )

        bot.send_message(
            message.chat.id,
            "مارا در صفحات مجازی دنبال کنید:",
            reply_markup=markup,
        )

    def about_us(message):
        text = """
🎓 انجمن علمی دانشجویی علوم کامپیوتر دانشگاه تبریز

ما یه جمع خودمونی از دانشجوهای علاقه‌مند به دنیای کامپیوتر و فناوری‌ایم 💻✨

اینجا توی انجمن علمی علوم کامپیوتر دانشگاه تبریز، دور هم جمع شدیم تا یاد بگیریم، یاد بدیم و با هم رشد کنیم 🚀

هدفمون ایجاد یه فضای پویاست برای یادگیری، اشتراک تجربه، برگزاری کارگاه‌ها، مسابقات، و کلی فعالیت خفن علمی و فرهنگی 📓

🔹 اعضای انجمن:
سیناپورمحمود(با تشکر از AI عزیز)

🔺 تشکر ویژه از:

➖ حسین حبیبی
بابت ایده ربات

➖ بهزاد پورمحمود
بابت تمامی حمایت‌های مادی و معنوی

🎁 راستی چون همه دانشجوی کامپیوتر هستیم، گفتیم که بد نیست پروژه رو به صورت متن‌باز قرار بدیم.

📍 انجمن علمی علوم کامپیوتر دانشگاه تبریز — جایی برای ایده‌ها، خلاقیت و دوستی 🤍
"""

        bot.send_message(
            message.chat.id,
            text,
        )

        send_document(
            message,
            "anjoman.pdf",
            "معرفی‌نامه انجمن علمی گروه علوم کامپیوتر دانشگاه تبریز",
        )

        bot.send_message(
            message.chat.id,
            "تهیه‌شده با ❤️",
        )


def format_price(price):
    if price is None:
        return "نامشخص"

    return f"{price:,}"