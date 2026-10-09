import io
import logging
import os

from telebot.apihelper import ApiException
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)

from db import Event, Registration, SessionLocal, User
from utils.code_generator import generate_unique_code

try:
    from openpyxl import Workbook
except ImportError:  # pragma: no cover - exercised only if the dep is missing
    Workbook = None


logger = logging.getLogger(__name__)


def _load_admin_ids():
    raw = os.getenv("ADMIN_TELEGRAM_IDS")
    if not raw:
        # Fallback defaults so existing deployments keep working even
        # without the env var set. Prefer setting ADMIN_TELEGRAM_IDS
        # (comma-separated Telegram user ids) in the environment instead
        # of editing this list.
        return {108738885, 428097665}

    ids = set()
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            ids.add(int(chunk))
        except ValueError:
            logger.warning("Ignoring invalid ADMIN_TELEGRAM_IDS entry: %r", chunk)

    return ids or {108738885, 428097665}


ADMIN_IDS = _load_admin_ids()


MAIN_MENU_BUTTONS = [
    "📍 مکان‌ها",
    "لیست دروس 📚",
    "🎬 برنامه‌ها",
    "🔗 لینک‌ها",
    "شماره‌ها 📞",
    "🌐 مجازی",
    "🍏 درباره ما 🚬",
]


def register_hello(bot):

    main_keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=False,
    )

    main_keyboard.row(
        "📍 مکان‌ها",
        "لیست دروس 📚",
    )

    main_keyboard.row("🎬 برنامه‌ها")

    main_keyboard.row(
        "🔗 لینک‌ها",
        "شماره‌ها 📞",
    )

    main_keyboard.row(
        "🌐 مجازی",
        "🍏 درباره ما 🚬",
    )

    @bot.message_handler(commands=["start"])
    def hello(message):
        with SessionLocal() as session:
            active_registration = (
                session.query(Registration)
                .join(Registration.event)
                .filter(
                    Registration.user.has(
                        User.tg_id == str(message.from_user.id)
                    ),
                    Event.code == "cinema",
                    Registration.status.in_(
                        ["collecting", "waiting_admin"]
                    ),
                )
                .first()
            )

        if active_registration:
            if active_registration.status == "collecting":
                markup = InlineKeyboardMarkup(row_width=1)
                markup.add(
                    InlineKeyboardButton(
                        "🔄 شروع دوباره ثبت‌نام سینما",
                        callback_data=(
                            f"register:{active_registration.registration_type}:cinema"
                        ),
                    )
                )
                bot.send_message(
                    message.chat.id,
                    (
                        "⏳ یک ثبت‌نام نیمه‌تمام پیدا شد. "
                        "برای شروع دوباره، دکمه زیر را بزنید."
                    ),
                    reply_markup=markup,
                )
                return

            bot.send_message(
                message.chat.id,
                (
                    "⛔ شما در حال انجام ثبت‌نام یک برنامه هستید.\n\n"
                    "اگر ثبت‌نامتان کامل شده، لطفاً منتظر بررسی ادمین بمانید."
                ),
            )
            return

        name = message.from_user.first_name or "دوست من"

        bot.send_message(
            message.chat.id,
            f"""
سلام {name} 👋

به ربات علوم کامپیوتر دانشگاه تبریز خوش اومدی.

👾 من یه ربات کمکی برای دانشجوهای رشته‌ی علوم کامپیوتر دانشگاه تبریزم.

اگه یه سر اومدی دانشگاه ولی نمی‌دونستی جایی که می‌خوای رو چطوری پیدا کنی، دکمه‌ی «📍 مکان‌ها» رو بزن.

یا اگه می‌خواستی بدونی چه درس‌هایی رو باید پاس کنی، دکمه‌ی «لیست دروس 📚» رو بزن.

لینک‌های مورد نیاز و شماره‌های مورد نیاز هم توی بخش‌های «🔗 لینک‌ها» و «شماره‌ها 📞» هستن.

همچنین می‌تونی از همین ربات برای برنامه سینما ثبت‌نام کنی. 🎬

می‌تونی چیزی که می‌خوای رو از منوی پایین پیدا کنی ☺️
""",
            reply_markup=main_keyboard,
        )

    @bot.message_handler(commands=["admin"])
    def admin_panel(message):
        if message.from_user.id not in ADMIN_IDS:
            bot.reply_to(
                message,
                "❌ شما اجازه دسترسی به پنل ادمین را ندارید.",
            )
            return

        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton(
                "⏳ ثبت‌نام‌های در انتظار تأیید",
                callback_data="admin_menu:pending",
            ),
            InlineKeyboardButton(
                "📊 اکسل ثبت‌نام‌های تأییدشده",
                callback_data="admin_menu:export",
            ),
        )
        bot.send_message(
            message.chat.id,
            "🛠 پنل ادمین\n\nیک گزینه را انتخاب کنید:",
            reply_markup=markup,
        )

    @bot.callback_query_handler(
        func=lambda call: call.data
        in {"admin_menu:pending", "admin_menu:export"}
    )
    def admin_menu(call):
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(
                call.id,
                "❌ شما اجازه انجام این کار را ندارید.",
            )
            return

        bot.answer_callback_query(call.id)

        if call.data == "admin_menu:pending":
            _send_pending_registrations(bot, call.message.chat.id)
        else:
            _send_approved_excel(bot, call.message.chat.id)

    @bot.callback_query_handler(
        func=lambda call: (
            call.data.startswith("approve:")
            or call.data.startswith("reject:")
        )
    )
    def admin_callback(call):
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(
                call.id,
                "❌ شما اجازه انجام این کار را ندارید.",
            )
            return

        action, registration_id_raw = call.data.split(":", 1)

        try:
            registration_id = int(registration_id_raw)
        except ValueError:
            bot.answer_callback_query(
                call.id,
                "❌ شناسه ثبت‌نام نامعتبر است.",
            )
            return

        with SessionLocal() as session:
            registration = (
                session.query(Registration)
                .filter(Registration.id == registration_id)
                .first()
            )

            if not registration:
                bot.answer_callback_query(
                    call.id,
                    "❌ ثبت‌نام پیدا نشد.",
                )
                return

            if registration.status != "waiting_admin":
                bot.answer_callback_query(
                    call.id,
                    "⚠️ این ثبت‌نام قبلاً بررسی شده است.",
                )
                return

            user = registration.user
            event = registration.event
            if event.code != "cinema":
                bot.answer_callback_query(
                    call.id,
                    "❌ در حال حاضر فقط ثبت‌نام سینما قابل بررسی است.",
                )
                return

            if action == "approve":
                registration.status = "approved"

                if not registration.ticket_code:
                    registration.ticket_code = generate_unique_code(
                        event.code
                    )

                session.commit()

                bot.answer_callback_query(
                    call.id,
                    "ثبت‌نام تأیید شد ✅",
                )

                try:
                    bot.send_message(
                        user.tg_id,
                        f"""
ثبت‌نامت با موفقیت تأیید شد ✅

🎉 برنامه: {event.name}

تو حالا رسماً مهمون ما هستی.

🎟 کد حضور شما:

{registration.ticket_code}

این کد رو تا روز برنامه نگه دار ❤️
منتظرت هستیم!
""",
                    )
                except ApiException:
                    logger.warning(
                        "Could not notify user %s about approval (registration %s).",
                        user.tg_id,
                        registration.id,
                    )

                try:
                    bot.edit_message_reply_markup(
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=None,
                    )
                except Exception:
                    pass

            else:
                registration.status = "rejected"
                session.commit()

                bot.answer_callback_query(
                    call.id,
                    "ثبت‌نام رد شد ❌",
                )

                try:
                    bot.send_message(
                        user.tg_id,
                        f"""
❌ پرداخت ثبت‌نام {event.name} تأیید نشد.

لطفاً اطلاعات پرداخت یا تصویر فیش را بررسی کنید و دوباره از بخش ثبت‌نام اقدام کنید.

اگر فکر می‌کنید اشتباهی رخ داده، با ادمین در ارتباط باشید.
""",
                    )
                except ApiException:
                    logger.warning(
                        "Could not notify user %s about rejection (registration %s).",
                        user.tg_id,
                        registration.id,
                    )

                try:
                    bot.edit_message_reply_markup(
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=None,
                    )
                except Exception:
                    pass

    return main_keyboard


def _send_pending_registrations(bot, chat_id):
    with SessionLocal() as session:
        registrations = (
            session.query(Registration)
            .join(Registration.user)
            .join(Registration.event)
            .filter(
                Registration.status == "waiting_admin",
                Event.code == "cinema",
            )
            .order_by(Registration.created_at.asc())
            .all()
        )

        if not registrations:
            bot.send_message(
                chat_id,
                "✅ هیچ ثبت‌نامی در انتظار بررسی نیست.",
            )
            return

        for registration in registrations:
            user = registration.user
            event = registration.event

            text = f"""
🎟 ثبت‌نام جدید

🎉 برنامه: {event.name}

👤 نام: {user.full_name or "نامشخص"}

📱 Telegram ID: {user.tg_id}

🎓 نوع ثبت‌نام: {"دانشجوی علوم کامپیوتر" if registration.registration_type == "student" else "مهمان"}

🆔 شماره دانشجویی: {user.student_id_card or "ندارد"}

👥 معرف: {registration.linked_student_id or "ندارد"}

💰 مبلغ:
{format_price(
    event.student_price
    if registration.registration_type == "student"
    else event.guest_price
)} تومان

📌 وضعیت: در انتظار بررسی
"""

            markup = InlineKeyboardMarkup(row_width=2)

            markup.add(
                InlineKeyboardButton(
                    "✅ تأیید",
                    callback_data=f"approve:{registration.id}",
                ),
                InlineKeyboardButton(
                    "❌ رد",
                    callback_data=f"reject:{registration.id}",
                ),
            )

            if registration.payment_proof_file_id:
                bot.send_photo(
                    chat_id,
                    registration.payment_proof_file_id,
                    caption=text,
                    reply_markup=markup,
                )
            else:
                bot.send_message(
                    chat_id,
                    text,
                    reply_markup=markup,
                )


def _send_approved_excel(bot, chat_id):
    if Workbook is None:
        bot.send_message(
            chat_id,
            "❌ ماژول openpyxl روی سرور نصب نیست.\n"
            "برای فعال‌سازی این قابلیت، دستور زیر را اجرا کنید:\n"
            "`pip install openpyxl`",
        )
        logger.error(
            "openpyxl is not installed; cannot export approved registrations."
        )
        return

    with SessionLocal() as session:
        registrations = (
            session.query(Registration)
            .join(Registration.user)
            .join(Registration.event)
            .filter(
                Registration.status == "approved",
                Event.code == "cinema",
            )
            .order_by(Registration.created_at.asc())
            .all()
        )

        rows = [
            (
                index,
                registration.user.full_name or "",
                "دانشجو"
                if registration.registration_type == "student"
                else "مهمان",
                registration.user.tg_id,
                registration.user.student_id_card or "",
                registration.linked_student_id or "",
                registration.ticket_code or "",
            )
            for index, registration in enumerate(registrations, start=1)
        ]

    if not rows:
        bot.send_message(
            chat_id,
            "✅ هنوز هیچ ثبت‌نام تأییدشده‌ای وجود ندارد.",
        )
        return

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Approved"
    sheet.append(
        [
            "ردیف",
            "نام و نام خانوادگی",
            "نوع ثبت‌نام",
            "آیدی تلگرام",
            "شماره دانشجویی",
            "آیدی معرف",
            "کد حضور",
        ]
    )
    for row in rows:
        sheet.append(list(row))

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    bot.send_document(
        chat_id,
        buffer,
        visible_file_name="cinema_approved_users.xlsx",
        caption=f"📊 {len(rows)} ثبت‌نام تأییدشده",
    )


def format_price(price):
    if price is None:
        return "نامشخص"

    return f"{price:,}"