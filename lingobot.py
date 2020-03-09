from time import gmtime, strftime, perf_counter as PF
import functools
from io import BytesIO
import ast
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters, CallbackQueryHandler
from telegram import Bot, Update, Message, CallbackQuery
import ui
from lessons import Lessons
from auth_token import token
# from recognition import recognition
from multiprocessing import Process
import logging
import subprocess
from ui import Content, Post
import global_vars
# initial global variables, DO THIS ONLY ONCE
global_vars.init()
# temporary log decoration
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
                print(global_vars.history)
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
    # @log()
    def run(self):
        self._updater.start_polling()
        self._updater.idle()

    # @log()
    def _post(self, update: Update, context: CallbackContext, post: Post, edit=True):
        
        editable = update.callback_query is not None
        if edit and editable:
            # Edit the previous message instead of sending a new one.
            content = post.get_content()
            message = update.callback_query.message
            if content.type == Content.Type.TEXT:
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
            if content.type == Content.Type.TEXT:
                message = bot.send_message(text=content.text,
                                 chat_id=update.effective_chat.id,
                                 reply_markup=post.get_markup(),
                                 parse_mode=post.parse_mode)
            elif content.type == Content.Type.VOICE:
                if type(content.file) is bytes:
                    file = BytesIO(content.file)
                    message = bot.send_voice(voice=file,
                                caption=content.text,
                                chat_id=update.effective_chat.id,
                                reply_markup=post.get_markup(),
                                parse_mode=post.parse_mode)
                else:
                    raise NotImplementedError
                    # TODO: files should be sent on another process
                    """
                    assert content.file_dir is not None
                    with open(content.file_dir, 'rb') as f:
                        message = bot.send_voice(voice=f,
                                    caption=content.text,
                                    chat_id=update.effective_chat.id,
                                    reply_markup=post.get_markup(),
                                    parse_mode=post.parse_mode)
                    """
            # print("Message sent:")
            # print(message.chat_id)
            # print(message.message_id)

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
        #clear history for user, incase start is pressed again:
        global_vars.history.clear_navigational_post(update._effective_user.id)
        self._post(update, context, ui.HomePost(update))

    @log()
    def _on_callback_query(self, update: Update, context: CallbackContext):
        query: CallbackQuery = update.callback_query
        callback_data: str = query.data
        # get a pointer to current post in chat for user 
        current_post = global_vars.history.get_navigational_post(update._effective_user.id).newest().post
        new_post: Post = None
        query_answer: str = ""
        #clear clutter if there is any
        global_vars.history.clear_removal_stack(context.bot, update)
        if callback_data == ui.Callback.BACK:
            assert isinstance(current_post, ui.BackSupportPost) or isinstance(current_post, ui.PageContainerPost)
            new_post = current_post.go_back()

        elif callback_data == ui.Callback.HOME:
            new_post = ui.HomePost(update)

        elif callback_data == ui.Callback.PLACEMENT_TEST:
            assert isinstance(current_post, ui.HomePost)
            new_post = ui.UnimplementedResponsePost(update)

        elif callback_data == ui.Callback.REVIEW_WORDS:
            assert isinstance(current_post, ui.HomePost)
            new_post = ui.UnimplementedResponsePost(update)

        elif callback_data == ui.Callback.CHOOSE_LESSON_POST:
            assert isinstance(current_post, ui.HomePost)
            new_post = ui.ChooseLessonPost(update)

        elif callback_data.startswith(ui.Callback.BASE_LESSON_STRING):
            assert isinstance(current_post, ui.ChooseLessonPost)
            lesson_id = int(
                callback_data[len(ui.Callback.BASE_LESSON_STRING):])
            new_post = ui.LessonPost(update, lesson_id)

        elif callback_data == ui.Callback.NARRATION:
            assert isinstance(current_post, ui.LessonPost)
            #remove previous clutter
            lesson_id = current_post.lesson_id
            new_post = ui.NarrationPost(update, lesson_id)
            query_answer = "Please be patient.."
        elif callback_data == ui.Callback.PRONUNCIATION_QUIZ:
            if isinstance(current_post, ui.PronunciationQuizPost):
                new_post = current_post
            else:
                assert isinstance(current_post, ui.LessonPost)
                lesson_id = current_post.lesson_id
                new_post = ui.PronunciationQuizPost(update, lesson_id)

        elif callback_data == ui.Callback.CLOZE_TEST:
            new_post = ui.UnimplementedResponsePost(update)

        elif callback_data == ui.Callback.NEXT_QUIZ_QUESTION:
            assert isinstance(current_post, ui.PronunciationQuizPost), print(
                current_post)
            current_post.next_page()
            new_post = current_post

        elif callback_data == ui.Callback.NEXT:
            assert isinstance(current_post, ui.PageContainerPost)
            current_post.next_page()
            new_post = current_post

        elif callback_data == ui.Callback.PREVIOUS:
            assert isinstance(current_post, ui.PageContainerPost)
            current_post.previous_page()
            new_post = current_post
        elif callback_data == ui.Callback.MESSAGE_CLEANUP:
            # assert isinstance(current_post, ui.GhostPost)
            global_vars.history.clear_removal_stack(context.bot, update)
        else:
            print(f'No callback found for: {callback_data}')
            new_post = ui.UnimplementedResponsePost(update, 
                'Sorry! An internal error occurred!')

        query.answer(query_answer)
        if new_post:
            self._post(update, context, new_post, edit=new_post.edit)
        # This doesn't work with the new history system. instead ... use the edit variable in Post class
        # print(f"+==============={new_post.type} :: {self.main_post.type}===============+")
        # if new_post.type == self.main_post.type:
        #     self._post(update, context, new_post)
        # else:
        #     self._post(update, context, new_post, edit=False)

    @log()
    def _on_voice_message(self, update: Update, context: CallbackContext):
        current_post = global_vars.history.get_navigational_post(update._effective_user.id).newest().post
        assert isinstance(current_post, ui.PronunciationQuizPost)
        word_num = current_post.page_idx

        message: Message = update.message
        
        message.voice.get_file().download('Audio/voice.ogg')
        output = subprocess.check_output(
            ['bash', '-c', 'ffmpeg -i Audio/voice.ogg -acodec pcm_s16le -ac 1 -ar 16000 -y Audio/out.wav'])
        output = recognition('Audio/out.wav')

        result = '<b><i>incorrect</i></b>'
        for word in output:
            if word.lower() == ui.lessons.get_by_id(current_post.lesson_id).vocab[word_num].lower().strip():
                result = '<b><i>correct</i></b>'

        msg = f'processed:\n{output}\n\nresult: {result}'
        new_post = ui.PronunciationResponsePost(update, 
            current_post.lesson_id, word_num, msg)

        self._post(update, context, new_post)
    @log()
    def _on_message(self, update: Update, context: CallbackContext):
        global_vars.history.clear_removal_stack(context.bot, update)
        msg = update.message.text
        if msg[0] == '/':
            #remove previous clutter
            # These clutter the screen, add them to removal stack
            global_vars.history.add_to_removal_stack(update)
            current_post = global_vars.history.get_navigational_post(update._effective_user.id).newest().post
            assert isinstance(current_post, ui.LessonPost)
            self._post(update, context, ui.PronunciationPost(update, msg[1:], current_post.lesson_id))
        else:
            self._post(update, context, ui.UnimplementedResponsePost(update))


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    lingo_bot = LingoBot()
    lingo_bot.run()
