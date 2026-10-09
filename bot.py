import logging
import os
import threading
import time

from dotenv import load_dotenv
from flask import Flask
import telebot
from telebot import apihelper

logger = logging.getLogger(__name__)

# How long to wait before restarting polling after it stops unexpectedly
# (e.g. a 409 Conflict - see the comment in run() below).
POLLING_RESTART_DELAY_SECONDS = 5

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

        # infinity_polling() is supposed to catch and retry on its own, but
        # its very first call - skip_pending's one-off "discard old updates"
        # request - happens *before* that retry loop starts, so an error
        # there (e.g. a 409 Conflict because another instance, like a local
        # test run, is polling with the same token - or Telegram briefly
        # seeing two pollers during a redeploy) escapes infinity_polling
        # entirely and would otherwise crash the whole process. Wrapping the
        # call ourselves means a crash there just waits a bit and tries
        # again, the same way infinity_polling already handles errors that
        # happen later, instead of relying on the host to restart the
        # container every time.
        while True:
            try:
                self.bot.infinity_polling(
                    timeout=30,
                    long_polling_timeout=20,
                    skip_pending=True,
                )
            except Exception:
                logger.exception(
                    "Polling stopped unexpectedly (e.g. a 409 Conflict from "
                    "another instance polling with the same token). "
                    "Retrying in %s seconds.",
                    POLLING_RESTART_DELAY_SECONDS,
                )
                time.sleep(POLLING_RESTART_DELAY_SECONDS)
            else:
                # infinity_polling only returns normally if something calls
                # stop_polling() - nothing here does, but exit cleanly
                # instead of looping forever if that ever changes.
                break


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