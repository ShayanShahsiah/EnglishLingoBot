from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters, CallbackQueryHandler
from telegram import Bot, Update, Message, CallbackQuery
import ui
from auth_token import token
from recognition import recognition

import logging
import subprocess

# temporary log decoration
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
                print(
                    f"Exiting \"{logText}\"\n\tTook {(end-start):.4f} seconds")
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
        self._word_num = 0
        self._lesson_num = None

    def run(self):
        self._updater.start_polling()
        self._updater.idle()

    def _add_handlers(self):
        self._dispatcher.add_handler(
            CommandHandler('start', self._on_command_start))

        self._dispatcher.add_handler(
            CallbackQueryHandler(self._on_callback_query))

        self._dispatcher.add_handler(MessageHandler(
            Filters.voice, self._on_voice_message))

        self._dispatcher.add_handler(
            MessageHandler(Filters.text, self._on_message))

    @log()
    def _post_message(self, update: Update, context: CallbackContext, msg: ui.Message, edit=True):
        # TODO: possibly should use inline_query instead of callback_query
        editable = update.callback_query != None
        if edit and editable:
            # Edit the previous message.
            update.callback_query.message.edit_text(msg.get_text(),
                                                    reply_markup=msg.get_markup(),
                                                    parse_mode=msg.parse_mode)
        else:
            # No edit. Send a new message.
            bot: Bot = context.bot
            bot.send_message(text=msg.get_text(),
                             chat_id=update.effective_chat.id,
                             reply_markup=msg.get_markup(),
                             parse_mode=msg.parse_mode)

    @log()
    def _on_command_start(self, update: Update, context: CallbackContext):
        home_message = ui.HomeMessage()
        self._post_message(update, context, home_message)

    @log()
    def _on_callback_query(self, update: Update, context: CallbackContext):
        query: CallbackQuery = update.callback_query
        callback_data: str = query.data

        if (callback_data == ui.Callback.HOME):
            self._on_select_return_home(update, context)
        elif (callback_data == ui.Callback.PLACEMENT_TEST):
            self._on_select_placement_test(update, context)
        elif (callback_data == ui.Callback.REVIEW_WORDS):
            self._on_select_review_words(update, context)
        elif (callback_data == ui.Callback.CHOOSE_LESSON):
            self._on_select_choose_lesson(update, context)
        elif (ui.Callback.LESSON_NUM in callback_data):
            self._on_select_lesson(update, context)
        elif (callback_data == ui.Callback.PRONUNCIATION_QUIZ):
            self._on_select_pronunciation_quiz(update, context)
        else:
            print('No matched callback')

        # answer queries, optional parameter to send notification as well
        query.answer()

    @log()
    def _on_select_placement_test(self, update: Update, context: CallbackContext):
        self._post_message(update, context, ui.UnimplementedResponseMessage())

    @log()
    def _on_select_review_words(self, update: Update, context: CallbackContext):
        self._post_message(update, context, ui.UnimplementedResponseMessage())

    @log()
    def _on_select_choose_lesson(self, update: Update, context: CallbackContext):
        choose_lesson_message = ui.ChooseLessonMessage()
        self._post_message(update, context, choose_lesson_message)

    @log()
    def _on_select_lesson(self, update: Update, context: CallbackContext):
        query: CallbackQuery = update.callback_query
        callback_data = query.data
        self._lesson_num = int(
            callback_data[len(ui.Callback.LESSON_NUM):])

        lesson_message = ui.LessonMessage(self._lesson_num)
        self._post_message(update, context, lesson_message)

    @log()
    def _on_select_pronunciation_quiz(self, update: Update, context: CallbackContext):
        pronunciation_quiz_message = ui.PronunciationQuizMessage(
            self._lesson_num, self._word_num)
        self._post_message(update, context, pronunciation_quiz_message)

    @log()
    def _on_voice_message(self, update: Update, context: CallbackContext):
        message: Message = update.message
        message.voice.get_file().download('Audio/voice.ogg')
        output = subprocess.check_output(
            ['bash', '-c', 'ffmpeg -i Audio/voice.ogg -acodec pcm_s16le -ac 1 -ar 16000 -y Audio/out.wav'])
        output = recognition('Audio/out.wav')

        result = '<b><i>incorrect</i></b>'
        for word in output:
            if word.lower() == ui.lessons[self._lesson_num].vocab[self._word_num].lower().strip():
                result = '<b><i>correct</i></b>'

        response_message = ui.PronunciationResponseMessage(
            self._lesson_num, self._word_num, str(output), result)

        self._post_message(update, context, response_message)

        if self._word_num < len(ui.lessons[self._lesson_num].vocab) - 1:
            self._word_num += 1
        else:
            self._word_num = 0

    def _on_select_return_home(self, update: Update, context: CallbackContext):
        message = ui.HomeMessage()
        self._post_message(update, context, message)

    @log()
    def _on_message(self, update: Update, context: CallbackContext):
        self._post_message(update, context, ui.UnimplementedResponseMessage())


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    lingo_bot = LingoBot()
    lingo_bot.run()
