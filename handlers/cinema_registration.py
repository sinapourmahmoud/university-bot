import logging
from functools import partial, wraps

from sqlalchemy.orm import Session

from db import Event, Registration, SessionLocal, User


logger = logging.getLogger(__name__)

EVENT_CODE = "cinema"
PERSIAN_DIGITS = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)


def _guard(handler):
    """Stop an unexpected error in a registration step from reaching
    telebot's polling loop or leaving the user stuck with no reply.

    Validation/business-logic failures in this module already return
    a friendly message on their own; this only catches the unexpected
    (a DB hiccup, a library bug, etc.), logs it, and tells the user to
    restart with /start instead of silently doing nothing or letting
    the exception bubble up to the bot's polling loop.
    """

    @wraps(handler)
    def wrapper(bot, message, *args, **kwargs):
        try:
            return handler(bot, message, *args, **kwargs)
        except Exception:
            logger.exception(
                "Unexpected error in cinema registration step %r for chat %s",
                handler.__name__,
                getattr(getattr(message, "chat", None), "id", "?"),
            )
            try:
                bot.send_message(
                    message.chat.id,
                    "⚠️ خطایی غیرمنتظره رخ داد. ثبت‌نام قطع شد. "
                    "لطفاً دوباره با /start شروع کنید.",
                )
            except Exception:
                logger.exception(
                    "Could not notify the user about the registration error."
                )

    return wrapper


@_guard
def begin_registration(bot, message, telegram_user_id, registration_type):
    if message.chat.type != "private":
        bot.send_message(
            message.chat.id,
            "برای ثبت‌نام سینما، لطفاً از گفت‌وگوی خصوصی ربات استفاده کنید.",
        )
        return

    if registration_type not in {"student", "guest"}:
        bot.send_message(message.chat.id, "❌ نوع ثبت‌نام نامعتبر است.")
        return

    tg_id = str(telegram_user_id)

    with SessionLocal() as session:
        event = (
            session.query(Event)
            .filter(
                Event.code == EVENT_CODE,
                Event.is_active.is_(True),
            )
            .first()
        )
        if not event:
            bot.send_message(
                message.chat.id,
                "❌ ثبت‌نام سینما در حال حاضر فعال نیست.",
            )
            return

        user = session.query(User).filter(User.tg_id == tg_id).first()
        if user is None:
            user = User(tg_id=tg_id)
            session.add(user)
            session.flush()

        registration = (
            session.query(Registration)
            .filter(
                Registration.user_id == user.id,
                Registration.event_id == event.id,
            )
            .first()
        )

        if registration and registration.status in {
            "approved",
            "waiting_admin",
        }:
            status_message = (
                "✅ ثبت‌نام شما قبلاً تأیید شده است."
                if registration.status == "approved"
                else "⏳ ثبت‌نام شما در انتظار بررسی ادمین است."
            )
            bot.send_message(message.chat.id, status_message)
            return

        if event.capacity is not None:
            active_count = (
                session.query(Registration)
                .filter(
                    Registration.event_id == event.id,
                    Registration.status.in_(
                        ["waiting_admin", "approved"]
                    ),
                )
                .count()
            )
            if active_count >= event.capacity:
                bot.send_message(
                    message.chat.id,
                    "⛔ ظرفیت ثبت‌نام سینما تکمیل شده است.",
                )
                return

        if registration is None:
            registration = Registration(
                user_id=user.id,
                event_id=event.id,
                registration_type=registration_type,
                status="collecting",
            )
            session.add(registration)
        else:
            registration.registration_type = registration_type
            registration.status = "collecting"
            registration.payment_proof_file_id = None
            registration.linked_student_id = None
            registration.ticket_code = None

        session.commit()

    if registration_type == "student":
        _ask(
            bot,
            message,
            "✍️ نام و نام خانوادگی خود را وارد کنید.\n"
            "برای لغو، exit یا /cancel را بفرستید.",
            save_student_name,
            EVENT_CODE,
        )
    else:
        _ask(
            bot,
            message,
            "✍️ نام و نام خانوادگی خود را وارد کنید.\n"
            "برای لغو، exit یا /cancel را بفرستید.",
            save_guest_name,
            EVENT_CODE,
        )


@_guard
def save_student_name(bot, message, event_code):
    if _is_exit(message):
        _cancel_registration(bot, message, event_code)
        return

    name = _message_text(message)
    if not 2 <= len(name) <= 255 or name.startswith("/"):
        _ask(
            bot,
            message,
            "❌ لطفاً نام و نام خانوادگی معتبر وارد کنید. "
            "برای لغو، exit یا /cancel را بفرستید.",
            save_student_name,
            event_code,
        )
        return

    with SessionLocal() as session:
        registration = _get_collecting_registration(
            session,
            message.from_user.id,
            event_code,
            "student",
        )
        if registration is None:
            _registration_expired(bot, message)
            return

        registration.user.full_name = name
        registration.user.is_student = True
        session.commit()

    _ask(
        bot,
        message,
        "🎓 شماره دانشجویی خود را وارد کنید (فقط عدد).",
        save_student_id,
        event_code,
    )


@_guard
def save_student_id(bot, message, event_code):
    if _is_exit(message):
        _cancel_registration(bot, message, event_code)
        return

    student_id = _message_text(message).translate(PERSIAN_DIGITS)
    if (
        not student_id.isascii()
        or not student_id.isdecimal()
        or len(student_id) > 32
    ):
        _ask(
            bot,
            message,
            "❌ شماره دانشجویی باید فقط شامل عدد باشد.",
            save_student_id,
            event_code,
        )
        return

    with SessionLocal() as session:
        registration = _get_collecting_registration(
            session,
            message.from_user.id,
            event_code,
            "student",
        )
        if registration is None:
            _registration_expired(bot, message)
            return

        registration.user.student_id_card = student_id
        registration.user.is_student = True
        session.commit()

    _request_payment_photo(bot, message, event_code)


@_guard
def save_guest_name(bot, message, event_code):
    if _is_exit(message):
        _cancel_registration(bot, message, event_code)
        return

    name = _message_text(message)
    if not 2 <= len(name) <= 255 or name.startswith("/"):
        _ask(
            bot,
            message,
            "❌ لطفاً نام و نام خانوادگی معتبر وارد کنید. "
            "برای لغو، exit یا /cancel را بفرستید.",
            save_guest_name,
            event_code,
        )
        return

    with SessionLocal() as session:
        registration = _get_collecting_registration(
            session,
            message.from_user.id,
            event_code,
            "guest",
        )
        if registration is None:
            _registration_expired(bot, message)
            return

        registration.user.full_name = name
        registration.user.is_student = False
        session.commit()

    _ask(
        bot,
        message,
        "🎓 شماره دانشجویی معرف خود را وارد کنید (فقط عدد).",
        save_guest_referrer,
        event_code,
    )


@_guard
def save_guest_referrer(bot, message, event_code):
    if _is_exit(message):
        _cancel_registration(bot, message, event_code)
        return

    student_id = _message_text(message).translate(PERSIAN_DIGITS)
    if (
        not student_id.isascii()
        or not student_id.isdecimal()
        or len(student_id) > 32
    ):
        _ask(
            bot,
            message,
            "❌ شماره دانشجویی معرف باید فقط شامل عدد باشد.",
            save_guest_referrer,
            event_code,
        )
        return

    tg_id = str(message.from_user.id)
    with SessionLocal() as session:
        registration = _get_collecting_registration(
            session,
            tg_id,
            event_code,
            "guest",
        )
        if registration is None:
            _registration_expired(bot, message)
            return

        referrer = (
            session.query(User)
            .join(User.registrations)
            .join(Registration.event)
            .filter(
                User.student_id_card == student_id,
                User.is_student.is_(True),
                Registration.registration_type == "student",
                Registration.status == "approved",
                Event.code == EVENT_CODE,
            )
            .first()
        )
        if referrer is None or referrer.tg_id == tg_id:
            _ask(
                bot,
                message,
                "❌ شماره‌ای با ثبت‌نام دانشجویی تأییدشده پیدا نشد. "
                "شماره معرف را دوباره وارد کنید.",
                save_guest_referrer,
                event_code,
            )
            return

        registration.linked_student_id = student_id
        session.commit()

    _request_payment_photo(bot, message, event_code)


@_guard
def save_payment_photo(bot, message, event_code):
    if _is_exit(message):
        _cancel_registration(bot, message, event_code)
        return

    if not message.photo:
        _ask(
            bot,
            message,
            "❌ لطفاً تصویر فیش را به صورت عکس ارسال کنید، "
            "یا برای لغو عبارت exit را بفرستید.",
            save_payment_photo,
            event_code,
        )
        return

    with SessionLocal() as session:
        registration = _get_collecting_registration(
            session,
            message.from_user.id,
            event_code,
        )
        if registration is None:
            _registration_expired(bot, message)
            return

        registration.payment_proof_file_id = message.photo[-1].file_id
        registration.status = "waiting_admin"
        session.commit()

    bot.send_message(
        message.chat.id,
        "✅ فیش پرداخت دریافت شد و ثبت‌نام شما برای بررسی ادمین ارسال شد. "
        "لطفاً تا دریافت نتیجه، دوباره ثبت‌نام نکنید. ❤️",
    )


def _get_collecting_registration(
    session: Session,
    telegram_user_id,
    event_code,
    registration_type=None,
):
    registration = (
        session.query(Registration)
        .join(Registration.user)
        .join(Registration.event)
        .filter(
            User.tg_id == str(telegram_user_id),
            Event.code == event_code,
            Registration.status == "collecting",
        )
        .first()
    )
    if (
        registration is not None
        and registration_type is not None
        and registration.registration_type != registration_type
    ):
        return None
    return registration


def _request_payment_photo(bot, message, event_code):
    _ask(
        bot,
        message,
        "💳 اطلاعات پرداخت\n\n"
        "لطفاً مبلغ ثبت‌نام را به حساب زیر واریز کنید:\n\n"
        "۶۱۰۴۳۳۷۵۶۵۲۳۳۹۹۴\n"
        "بانک ملت\n"
        "به نام: بهزاد پورمحمود آقابابا\n\n"
        "سپس تصویر واضح فیش را به صورت عکس ارسال کنید. "
        "برای لغو، exit یا /cancel را بفرستید.",
        save_payment_photo,
        event_code,
    )


def _cancel_registration(bot, message, event_code):
    with SessionLocal() as session:
        registration = _get_collecting_registration(
            session,
            message.from_user.id,
            event_code,
        )
        if registration is None:
            _registration_expired(bot, message)
            return

        registration.status = "cancelled"
        registration.linked_student_id = None
        registration.payment_proof_file_id = None
        session.commit()

    bot.send_message(message.chat.id, "❌ ثبت‌نام سینما لغو شد.")


def _registration_expired(bot, message):
    bot.send_message(
        message.chat.id,
        "❌ فرایند ثبت‌نام پیدا نشد یا دیگر فعال نیست. "
        "لطفاً دوباره از منوی سینما شروع کنید.",
    )


def _ask(bot, message, prompt, handler, event_code):
    bot.send_message(message.chat.id, prompt)
    bot.register_next_step_handler(
        message,
        partial(handler, bot),
        event_code,
    )


def _message_text(message):
    return (message.text or "").strip()


def _is_exit(message):
    text = _message_text(message).casefold()
    command = text.split("@", 1)[0]
    return text in {"exit", "cancel", "لغو", "خروج"} or command in {
        "/cancel",
        "/exit",
        "/start",
    }
