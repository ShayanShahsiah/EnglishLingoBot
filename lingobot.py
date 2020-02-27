from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters, CallbackQueryHandler
from telegram import Bot, Update, Message, CallbackQuery
from ui import Interface
from auth_token import token
import logging

#temporary log decoration
import functools
from time import gmtime, strftime, perf_counter as PF

def log(verbose=True):
    def logger(function):
        @functools.wraps(function)
        def wrapper_logger(*args, **kwargs):
            logText = function.__name__
            print(f"Entering \"{logText}\"")
            if verbose:
                try:
                    data = f'\tAt {strftime("%H:%M:%S", gmtime())}\n\tUser = {args[1]["_effective_user"]["first_name"]}\n\tUpdate ID: {args[1]["update_id"]}' 
                except:
                    data = f'\tAt {strftime("%H:%M:%S", gmtime())}'
                finally:
                    print(data)
                start = PF()
                value = function(*args, **kwargs)
                end = PF()
                print(f"Exiting \"{logText}\"\n\tTook {(end-start):.4f} seconds")
            else:
                value = function(*args, **kwargs)
                print(f"Exiting \"{logText}\"")
            return value
        return wrapper_logger
    return logger

class LingoBot:
    def __init__(self):
        self._updater = Updater(token=token, use_context=True)
        self._dispatcher = self._updater.dispatcher
        self._add_handlers()
        self._message_history = []

    def run(self):
        self._updater.start_polling()
        self._updater.idle()
    

    def _save_message_to_history(handler_method):
        def handler(self, update: Update, context: CallbackContext):
            incoming_message = update.message
            if incoming_message:
                self._message_history.append(incoming_message)
            outgoing_message = handler_method(self, update, context)
            if outgoing_message:
                self._message_history.append(outgoing_message)
        return handler

    def _add_handlers(self):
        self._dispatcher.add_handler(CommandHandler('start', self._on_command_start))
        self._dispatcher.add_handler(CommandHandler('stop', self._on_command_stop))
        self._dispatcher.add_handler(CallbackQueryHandler(self._on_callback_query))
        self._dispatcher.add_handler(MessageHandler(Filters.text, self._on_message))

    @log()
    @_save_message_to_history
    def _on_command_start(self, update: Update, context: CallbackContext):
        #delete previous messages to keep things neat!
        while len(self._message_history) > 0:
            self._message_history.pop().delete()

        message: Message = update.message
        return message.reply_text(Interface.home_text, reply_markup=Interface.home_markup)

    @_save_message_to_history
    def _on_command_stop(self, update: Update, context: CallbackContext):
        message: Message = update.message
        return message.reply_text("Nothing to do for now lulz!")

    @log()
    def _on_callback_query(self, update: Update, context: CallbackContext):
        query: CallbackQuery = update.callback_query
        callback_data: str = query.data
        if (callback_data == Interface.CALLBACK_HOME):
            self._on_return_home(update, context)
            #answer queries, optional parameter to send notification as well
            query.answer()
        elif (callback_data == Interface.CALLBACK_PLACEMENT_TEST):
            self._on_select_placement_test(update, context)
            query.answer()
        elif (callback_data == Interface.CALLBACK_REVIEW_WORDS):
            self._on_select_review_words(update, context)
            query.answer()
        elif (callback_data == Interface.CALLBACK_CHOOSE_LESSON):
            query.answer()
            self._on_select_choose_lesson(update, context)
        elif (Interface.CALLBACK_LESSON_NUM in callback_data):
            self._on_select_lesson(update, context)
            query.answer()

    @log()
    @_save_message_to_history
    def _on_select_placement_test(self, update: Update, context: CallbackContext):
        bot: Bot = context.bot
        return bot.send_message(chat_id=update.effective_chat.id, text="I don't know how to deal with that yet!")
    
    @log()
    @_save_message_to_history
    def _on_select_review_words(self, update: Update, context: CallbackContext):
        bot: Bot = context.bot
        return bot.send_message(chat_id=update.effective_chat.id, text="I don't know how to deal with that yet!")
    
    @log()
    def _on_select_choose_lesson(self, update: Update, context: CallbackContext):
        query: CallbackQuery = update.callback_query
        query.message.edit_text(Interface.choose_lesson_text, reply_markup=Interface.choose_lesson_markup)
    
    @log()
    def _on_select_lesson(self, update: Update, context: CallbackContext):
        query: CallbackQuery = update.callback_query
        callback_data = query.data
        lesson_num = int(callback_data[len(Interface.CALLBACK_LESSON_NUM):])
        query.message.edit_text(Interface.lesson_text(lesson_num), reply_markup=Interface.lesson_markup)

    def _on_return_home(self, update: Update, context: CallbackContext):
        query: CallbackQuery = update.callback_query
        query.message.edit_text(Interface.home_text, reply_markup=Interface.home_markup)
    
    @log()
    @_save_message_to_history
    def _on_message(self, update: Update, context: CallbackContext):
        message: Message = update.message
        return message.reply_text("I don't know how to deal with that yet!")

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    lingo_bot = LingoBot()
    lingo_bot.run()