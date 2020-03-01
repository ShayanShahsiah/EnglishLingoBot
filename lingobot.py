from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters, CallbackQueryHandler
from telegram import Bot, Update, Message, CallbackQuery
import ui
from lessons import Lessons
from auth_token import token
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
        #these variables should exist for each user seperately, 
        #fix this when database is available
        self.currentLesson: Lesson = None
        self.lessonHandler: ui.ChooseLessonPost = None
        ########
    @log()
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
    def _post(self, update: Update, context: CallbackContext, post: ui.Post, edit=True):
        # TODO: possibly should use inline_query instead of callback_query
        editable = update.callback_query != None
        if edit and editable:
            # Edit the previous message instead of sending a new one.
            content = post.get_content()
            message = update.callback_query.message
            if content.file_type == ui.Content.FileType.TEXT:
                message.edit_text(content.text,
                                  reply_markup=post.get_markup(),
                                  parse_mode=post.parse_mode)
            else:
                # TODO: Edit a message and add file (e.g. voice) if possible?
                pass

        else:
            # Don't edit. Send a new message.
            content = post.get_content()
            bot: Bot = context.bot
            if content.file_type == ui.Content.FileType.TEXT:
                bot.send_message(text=content.text,
                                 chat_id=update.effective_chat.id,
                                 reply_markup=post.get_markup(),
                                 parse_mode=post.parse_mode)
            elif content.file_type == ui.Content.FileType.VOICE:
                with open(content.file_dir, 'rb') as f:
                    bot.send_voice(voice=f,
                                   chat_id=update.effective_chat.id,
                                   reply_markup=post.get_markup(),
                                   parse_mode=post.parse_mode)

    @log()
    def _on_command_start(self, update: Update, context: CallbackContext):
        post = ui.HomePost()
        self._post(update, context, post)

    @log()
    def _on_callback_query(self, update: Update, context: CallbackContext):
        query: CallbackQuery = update.callback_query
        callback_data: str = query.data

        if callback_data == ui.Callback.HOME:
            self._on_select_return_home(update, context)
            query.answer()
        elif callback_data == ui.Callback.PLACEMENT_TEST:
            self._on_select_placement_test(update, context)
            query.answer()
        elif callback_data == ui.Callback.REVIEW_WORDS:
            self._on_select_review_words(update, context)
            query.answer()
        elif callback_data in {ui.Callback.CHOOSE_LESSON, ui.Callback.NEXT_LESSON_PAGE,ui.Callback.PREV_LESSON_PAGE} :
            if ui.Callback.CHOOSE_LESSON in callback_data:
                self.lessonHandler = self._on_select_choose_lesson(update, context)
                query.answer()
            elif self.lessonHandler is None:
                query.answer("Lesson data don't exist. Go back or pick a story")
            elif ui.Callback.NEXT_LESSON_PAGE in callback_data:
                self._on_select_next_or_prev_lesson(update, context, self.lessonHandler, direction=True)
                query.answer()
            elif ui.Callback.PREV_LESSON_PAGE in callback_data:
                self._on_select_next_or_prev_lesson(update, context, self.lessonHandler, direction=False)
                query.answer()
        elif callback_data == ui.Callback.NARRATION:
            self._on_select_narration(update, context)
            query.answer()
        elif callback_data == ui.Callback.PRONUNCIATION_QUIZ:
            self._on_select_pronunciation_quiz(update, context)
            query.answer()
        elif ui.Callback.BASE_LESSON_STRING in callback_data:
            self._on_select_lesson(update, context)
        else:
            print('No matched callback')
            print(callback_data)
            query.answer()


    @log()
    def _on_select_placement_test(self, update: Update, context: CallbackContext):
        post = ui.UnimplementedResponsePost()
        self._post(update, context, post)

    @log()
    def _on_select_review_words(self, update: Update, context: CallbackContext):
        post = ui.UnimplementedResponsePost()
        self._post(update, context, post)

    @log()
    def _on_select_choose_lesson(self, update: Update, context: CallbackContext):
        lessons = Lessons()
        post = ui.ChooseLessonPost(lessons.getNRandom(count=10))
        self._post(update, context, post)
        return post
    def _on_select_next_or_prev_lesson(self, update: Update, context: CallbackContext, lessonHandler: ui.ChooseLessonPost, direction):
        """
        True to go next
        False to go prev
        """
        if direction:
            post = lessonHandler.go_next_page()
        else:
            post = lessonHandler.go_prev_page()
        if post is None:
            return
        self._post(update, context, post)

    @log()
    def _on_select_lesson(self, update: Update, context: CallbackContext):
        query: CallbackQuery = update.callback_query
        callback_data = query.data
        lesson_num = int(callback_data.replace(ui.Callback.BASE_LESSON_STRING, ''))
        lessons = Lessons()
        self.currentLesson = lessons.getByID(lesson_num)
        post = ui.LessonPost(self.currentLesson)
        self._post(update, context, post)

    @log()
    def _on_select_narration(self, update: Update, context: CallbackContext):
        post = ui.NarrationPost(self._lesson_num)
        self._post(update, context, post, edit=False)

    @log()
    def _on_select_pronunciation_quiz(self, update: Update, context: CallbackContext):
        post = ui.PronunciationQuizPost(self.currentLesson)
        self._post(update, context, post)

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

        post = ui.PronunciationResponsePost(
            self._lesson_num, self._word_num, str(output), result)

        self._post(update, context, post)

        if self._word_num < len(ui.lessons[self._lesson_num].vocab) - 1:
            self._word_num += 1
        else:
            self._word_num = 0

    @log()
    def _on_select_return_home(self, update: Update, context: CallbackContext):
        post = ui.HomePost()
        self._post(update, context, post)

    @log()
    def _on_message(self, update: Update, context: CallbackContext):
        post = ui.UnimplementedResponsePost()
        self._post(update, context, post)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    lingo_bot = LingoBot()
    lingo_bot.run()
