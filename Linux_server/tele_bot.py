from telegram.ext import Updater
from telegram.ext import CommandHandler,MessageHandler,Filters
import re
import telegram,threading
import zmq



def ident(dat):
    return dat
def async_(target, args=(), kwargs={}):
    thread=threading.Thread(target=target, args=args, kwargs=kwargs)
    thread.daemon = True
    thread.start()
    return thread

class Tel_Bot(object):
    def __init__(self,token,channel_id,port):
        self.updater = Updater(token=token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.channel_id = channel_id
        self.bot = telegram.Bot(token)
        ctx = zmq.Context.instance()
        self.sock = ctx.socket(zmq.REP)
        self.sock.bind(f'tcp://*:{port}')

        #f"https://api.telegram.org/bot{token}/sendMessage?chat_id=@{channel_id}&text=123"
        self.message_func = {}
        self.comm_re = {'d1':re.compile('\d{1}')}
        self.comm_func = {'d1':ident}
        async_(self.message_get)
    # command hander
    def message_get(self):
        while True:
            message = self.sock.recv_string()
            self.bot.send_message(chat_id=self.channel_id,text=message)
            #self.sock.send_string("Telegram seding comp")

    def run(self):
        def comm_start(update, context):
            context.bot.send_message(chat_id=self.channel_id,text="I'm a bot, please talk to me!")
        def message_func_start(update, context):
            text = ''
            given_text = update.message.text
            if len(given_text) ==1:
                if self.comm_re['d1'].match(given_text) is not None:
                    text += self.comm_func['d1'](given_text)
            else:
                text = (given_text +"\n")*10
            context.bot.send_message(chat_id=self.channel_id,text=text)
            #update.effective_chat.id
        start_handler = CommandHandler('start', comm_start)
        self.dispatcher.add_handler(start_handler)

        message_handler = MessageHandler(Filters.text & (~Filters.command), message_func_start)
        self.dispatcher.add_handler(message_handler)
        self.updater.start_polling()
