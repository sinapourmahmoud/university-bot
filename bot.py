import telebot
from handlers.register_hello import register_hello
from handlers.button_handlers import register_buttons
import os
from flask import Flask
import threading
from dotenv import load_dotenv
# Load environment variables
load_dotenv()
# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 University Bot is running successfully!"

def run_web():
    # Run Flask on port 8080 (standard for Replit)
    app.run(host='0.0.0.0', port=8080)

# Initialize Telegram Bot
class UniversityBot:
    def __init__(self):
        token = os.getenv('BOT_TOKEN')
        
        self.bot = telebot.TeleBot(token)
        self._register_handlers()
    
    def _register_handlers(self):
        register_hello(self.bot)
        register_buttons(self.bot)

    def run(self):
        print("🚀 Bot started successfully and is now polling...")
        self.bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    # Run Flask server in a background thread
    threading.Thread(target=run_web, daemon=True).start()
    
    # Start the bot
    university = UniversityBot()
    university.run()
