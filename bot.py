import os
import threading

from dotenv import load_dotenv
from flask import Flask
import telebot
from telebot import apihelper

load_dotenv()

# Telegram's API is reached over a VPN/filtered connection for every user in
# Iran, which makes a transient SSL/connection error (SSLEOFError, "Connection
# reset", etc.) fairly common on any single API call - regardless of whose
# VPN or ISP it is. pyTelegramBotAPI ships with automatic retries turned off
# by default, so without this a single hiccup crashes whichever handler was
# sending a message (e.g. the SSLError seen on /start). Turning retries on
# makes the bot quietly retry a few times instead of failing on the first
# blip.
apihelper.RETRY_ON_ERROR = True
apihelper.MAX_RETRIES = 5
apihelper.RETRY_TIMEOUT = 2

from db import init_db
from handlers.register_hello import register_hello
from handlers.button_handlers import register_buttons


app = Flask(__name__)


@app.route("/")
def home():
    return "🤖 University Bot is running successfully!"


@app.route("/health")
def health():
    return {"status": "ok"}, 200


def run_web():
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)


class UniversityBot:
    def __init__(self):
        token = os.getenv("BOT_TOKEN")

        if not token:
            raise RuntimeError(
                "BOT_TOKEN is not set. Please configure it in your environment."
            )

        self.bot = telebot.TeleBot(token)

        self._register_handlers()

    def _register_handlers(self):
        register_hello(self.bot)
        register_buttons(self.bot)

    def run(self):
        print("🚀 University Bot started successfully.")

        self.bot.infinity_polling(
            timeout=30,
            long_polling_timeout=20,
            skip_pending=True,
        )


def main():
    init_db()

    threading.Thread(
        target=run_web,
        daemon=True,
        name="health-server",
    ).start()

    university = UniversityBot()
    university.run()


if __name__ == "__main__":
    main()