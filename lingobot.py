from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters, CallbackQueryHandler
# TODO: possibly should use inline_query instead of callback_query
from telegram import Bot, Update, Message, CallbackQuery
import ui
from auth_token import token
from io import BytesIO
# from recognition import recognition

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
        self._lesson_id: int

        self.main_post: ui.Post

    @log()
    def run(self):
        self._updater.start_polling()
        self._updater.idle()

    @log()
    def _post(self, update: Update, context: CallbackContext, post: ui.Post, edit=True):
        editable = update.callback_query is not None
        if edit and editable:
            # Edit the previous message instead of sending a new one.
            content = post.get_content()
            message = update.callback_query.message
            if content.type == ui.Content.Type.TEXT:
                message.edit_text(content.data,
                                  reply_markup=post.get_markup(),
                                  parse_mode=post.parse_mode)
            else:
                # TODO: Edit a message and add file (e.g. voice) if possible?
                pass

        else:
            # Don't edit. Send a new message.
            content = post.get_content()
            bot: Bot = context.bot
            if content.type == ui.Content.Type.TEXT:
                bot.send_message(text=content.data,
                                 chat_id=update.effective_chat.id,
                                 reply_markup=post.get_markup(),
                                 parse_mode=post.parse_mode)
            elif content.type == ui.Content.Type.VOICE:
                if type(content.data) is bytes:
                    data = BytesIO(content.data)
                    bot.send_voice(voice=data,
                                chat_id=update.effective_chat.id,
                                reply_markup=post.get_markup(),
                                parse_mode=post.parse_mode)
                # Deprecated
                # else:
                #     assert content.file_dir is not None
                #     with open(content.file_dir, 'rb') as f:
                #         bot.send_voice(voice=f,
                #                     chat_id=update.effective_chat.id,
                #                     reply_markup=post.get_markup(),
                #                     parse_mode=post.parse_mode)

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
    def _on_command_start(self, update: Update, context: CallbackContext):
        self.main_post = ui.HomePost()
        self._post(update, context, self.main_post)
        print('dyh!')

    @log()
    def _on_callback_query(self, update: Update, context: CallbackContext):
        query: CallbackQuery = update.callback_query
        callback_data: str = query.data
        new_post: ui.Post
        query_answer: str = ""
        if callback_data == ui.Callback.BACK:
            assert isinstance(self.main_post, ui.BackSupportPost)
            self.main_post = self.main_post.get_previous_post()
            new_post = self.main_post

        elif callback_data == ui.Callback.HOME:
            self.main_post = ui.HomePost()
            new_post = self.main_post

        elif callback_data == ui.Callback.PLACEMENT_TEST:
            self.main_post = ui.UnimplementedResponsePost()
            new_post = self.main_post

        elif callback_data == ui.Callback.REVIEW_WORDS:
            self.main_post = ui.UnimplementedResponsePost()
            new_post = self.main_post

        elif callback_data == ui.Callback.CHOOSE_LESSON_POST:
            self.main_post = ui.ChooseLessonPost()
            new_post = self.main_post


        elif callback_data.startswith(ui.Callback.BASE_LESSON_STRING):
            lesson_id = int(
                callback_data[len(ui.Callback.BASE_LESSON_STRING):])
            self._lesson_id = lesson_id
            self.main_post = ui.LessonPost(lesson_id)
            new_post = self.main_post

        elif callback_data == ui.Callback.NARRATION:
            assert isinstance(self.main_post, ui.LessonPost)
            lesson_id = self.main_post.lesson_id
            new_post = ui.NarrationPost(lesson_id)
            query_answer = "Please be patient.."
        elif callback_data == ui.Callback.PRONUNCIATION_QUIZ:
            if isinstance(self.main_post, ui.PronunciationQuizPost):
                new_post = self.main_post
            else:
                assert isinstance(self.main_post, ui.LessonPost)
                lesson_id = self.main_post.lesson_id
                self.main_post = ui.PronunciationQuizPost(lesson_id)
                new_post = self.main_post

        elif callback_data == ui.Callback.CLOZE_TEST:
            self.main_post = ui.UnimplementedResponsePost()
            new_post = self.main_post

        elif callback_data == ui.Callback.NEXT_QUIZ_QUESTION:
            assert isinstance(self.main_post, ui.PronunciationQuizPost), print(self.main_post)
            self.main_post.go_next()
            new_post = self.main_post

        elif callback_data == ui.Callback.NEXT:
            assert isinstance(self.main_post, ui.PageContainerPost)
            self.main_post.go_next()
            new_post = self.main_post

        elif callback_data == ui.Callback.PREVIOUS:
            assert isinstance(self.main_post, ui.PageContainerPost)
            self.main_post.go_previous()
            new_post = self.main_post

        else:
            print(f'No callback found for: {callback_data}')
            self.main_post = ui.UnimplementedResponsePost(
                'Sorry! An internal error occurred!')
            new_post = self.main_post

        query.answer(query_answer)
        if new_post is self.main_post:
            self._post(update, context, new_post)
        else:
            self._post(update, context, new_post, edit=False)

    @log()
    def _on_voice_message(self, update: Update, context: CallbackContext):
        assert isinstance(self.main_post, ui.PronunciationQuizPost)
        word_num = self.main_post.page_idx

        message: Message = update.message
        message.voice.get_file().download('Audio/voice.ogg')
        output = subprocess.check_output(
            ['bash', '-c', 'ffmpeg -i Audio/voice.ogg -acodec pcm_s16le -ac 1 -ar 16000 -y Audio/out.wav'])
        output = recognition('Audio/out.wav')

        result = '<b><i>incorrect</i></b>'
        for word in output:
            if word.lower() == ui.lessons.get_by_id(self._lesson_id).vocab[word_num].lower().strip():
                result = '<b><i>correct</i></b>'

        msg = f'processed:\n{output}\n\nresult: {result}'
        new_post = ui.PronunciationResponsePost(
            self._lesson_id, word_num, msg)

        self._post(update, context, new_post)

    @log()
    def _on_message(self, update: Update, context: CallbackContext):
        self.main_post = ui.UnimplementedResponsePost()
        self._post(update, context, self.main_post)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    lingo_bot = LingoBot()
    lingo_bot.run()
