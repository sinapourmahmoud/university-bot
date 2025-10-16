import telebot
from handlers.register_hello import register_hello
from handlers.button_handlers import register_buttons
class UniversityBot():
    
    def __init__(self):
        self.bot=telebot.TeleBot('7957636569:AAHjRB7tvPXCtSING70W6FlGyz75HTp0trk')
        self.handlers()
        
    def handlers(self):
        register_hello(self.bot)

        register_buttons(self.bot)
        
    
    
    def end(self):
        self.bot.polling()
    
    
if __name__=="__main__":
    university=UniversityBot()
    university.end()
    