import telebot
from handlers.register_hello import register_hello
from handlers.button_handlers import register_buttons
import dotenv
import os
from flask import Flask
import threading

dotenv.load_dotenv()

class UniversityBot:
    def __init__(self):
        self.bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
        self._register_handlers()
    
    def _register_handlers(self):
        register_hello(self.bot)
        register_buttons(self.bot)

    def run(self):
        self.bot.polling(non_stop=True)

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 University Bot is running successfully!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    
    university = UniversityBot()
    university.run()
