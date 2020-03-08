from telegram import InlineKeyboardMarkup as IKMarkup, InlineKeyboardButton as IKButton, Update
from synthesis import Synthesis
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Optional, Union, Dict
import globals
from abc import abstractmethod
DISPLAYED_LESSONS = 30
LESSONS_PER_PAGE = 6

class Callback():

    BACK = 'BACK'

    HOME = 'HOME'
    PLACEMENT_TEST = 'PLACEMENT_TEST'
    REVIEW_WORDS = 'REVIEW_WORDS'

    CHOOSE_LESSON_POST = 'CHOOSE_LESSON_POST'
    NEXT_LESSON_POST = "NEXT_LESSON_POST"
    PREV_LESSON_POST = "PREV_LESSON_POST"

    # The lesson index is appended to base string here:
    BASE_LESSON_STRING = 'LESSON_NUM_'

    NARRATION = 'NARRATION'
    PRONUNCIATION_QUIZ = 'PRONUNCIATION_QUIZ'
    CLOZE_TEST = 'CLOZE_TEST'

    NEXT_QUIZ_QUESTION = 'NEXT_QUIZ_QUESTION'

    NEXT = 'PAGE_CONTAINER_NEXT'
    PREVIOUS = 'PAGE_CONTAINER_PREVIOUS'

    MESSAGE_CLEANUP = 'MESSAGE_CLEANUP'
class Content():
    """
    Container class for the contents of a Post.

    Attributes:
        text (Optional[str]): String or Bytes to send
        file (Optional[Union[str, bytes]]): file directory or content bytes for multimedia messages.
        type (Content.Type): Type of content (currently TEXT, VOICE, PHOTO).
    """
    class Type(Enum):
        TEXT = auto()
        VOICE = auto()
        PHOTO = auto()

    def __init__(self, text: Optional[str] = None, file: Optional[Union[str, bytes]] = None,
                 type: 'Type' = Type.TEXT):

        self.text = text
        self.file = file
        self.type = type
    def __repr__(self):
        safetext = self.text[:30].replace('\n', ' ') + '...'
        return f"\n\t\tText: {safetext}\n\t\tfileType: {type(self.file)}\n\t\ttype: {self.type}"
class Post(ABC):
    """
    Abstract base class for all posts.
    """

    def __init__(self, update: Update):
        self.owner_id = update._effective_user.id
        self.chat_id = update._effective_chat.id
        #this is not the message id for this post, only current message
        self._message_id = update._effective_message.message_id
        self.parse_mode: str = 'html'
        self.edit: bool = True
        self.type: str = self.__class__.__name__
        self.add_to_removal_stack = False
        self.add_to_navigational_stack = True
    def _update_history(self):
        #append to history or removal stack
        if self.add_to_navigational_stack:
            globals.history.make_navigational_post(self.owner_id)
            globals.history.add_navigational_post(self, self.owner_id)
        if self.add_to_removal_stack:
            # normally this post would be right after update, 
            # but if multiple posts are sent at once, it can be after that
            # try to add until successful
            message_id = self._message_id + 1
            while True:
                if globals.history.add_to_removal_stack(self.chat_id, message_id, self.owner_id):
                    break
                message_id += 1
        
    @abstractmethod
    def get_content(self) -> Content:
        pass
    @abstractmethod
    def get_markup(self) -> IKMarkup:
        pass


class BasicPost(Post):
    """
    Abstract base class for posts that don't support navigation to the previous post.
    """
    def __init__(self, update: Update):
        super().__init__(update)
        self._update_history()
    

class HomePost(BasicPost):
    def __init__(self, update: Update):
        super().__init__(update)
    def get_content(self):
        return Content(text='سلام. به روبات آموزش زبان خوش آمدید! برای شروع لطفاً یکی از موارد زیر را انتخاب کنید')
    def get_markup(self):
        return IKMarkup([
            [IKButton('آزمون تعیین سطح', callback_data=Callback.PLACEMENT_TEST)],
            [IKButton('درس‌ها', callback_data=Callback.CHOOSE_LESSON_POST)],
            [IKButton('لغات ستاره‌دار', callback_data=Callback.REVIEW_WORDS)]])

class BackSupportPost(Post):
    """
    Abstract base class for posts that support navigation to the previous post.
    """
    def __init__(self, update: Update):
        super().__init__(update)
        self._update_history()

    def go_back(self) -> Post:
        return globals.history.get_navigational_post(self.owner_id).previous().post

    def get_markup(self) -> IKMarkup:
        return IKMarkup([[IKButton('بازگشت', callback_data=Callback.BACK)]])
class LessonPost(BackSupportPost):
    def __init__(self, update: Update, lesson_id):
        self.lesson_id = lesson_id
        self.vocab_available = globals.lessons.get_by_id(self.lesson_id).vocab is not None
        self.text = self._slashify()
        super().__init__(update)

    def _slashify(self) -> str:
        text = globals.lessons.get_by_id(self.lesson_id).text
        #copy without sharing memory:
        try:
            vocab = globals.lessons.get_by_id(self.lesson_id).vocab[:]
        except TypeError:
            return text
        
        words: List[str] = text.split()
        for i in range(len(words)):
            matched = False
            for j in range(len(vocab)):
                if vocab[j] != '' and words[i].startswith(vocab[j]):
                    matched = True
                    vocab[j] = ''
                    break
            if matched:
                words[i] = '/' + words[i]

        return ' '.join(words)

    def get_content(self) -> Content:
        text = "<b>{}</b>\n\n{}".format(
            globals.lessons.get_by_id(self.lesson_id).name, self.text)
        if not self.vocab_available:
            text += '\n\n <i>Pronunciation quiz not available for this lesson.</i>'
        return Content(text=text)

    def get_markup(self) -> IKMarkup:
        buttons = [
            [IKButton('Listen to Narration', callback_data=Callback.NARRATION)]]
        if self.vocab_available:
            buttons += [[IKButton('Pronunciation Quiz',
                                  callback_data=Callback.PRONUNCIATION_QUIZ)]]

        return IKMarkup(buttons + super().get_markup().inline_keyboard)
class UnimplementedResponsePost(BackSupportPost):
    def __init__(self, update, text="Sry don't know how to respond to that!"):
        self.text = text
        super().__init__(update)

    def get_content(self):
        return Content(text=self.text)

class GhostPost(Post):
    """
    Abstract base class for posts that are outside the back navigation stack.

    Could for example be used for a short message sent after a bigger "main" message
    without affecting the "back button" functionality of the older message.

    Messages using this class can clump up and decrease visability, so a special markup is used to remove them
    """
    def __init__(self, update: Update):
        super().__init__(update)
        # Doesn't affect the global navigation stack
        self.add_to_navigational_stack = False
        # Does affect cleanup stack(if specified in self.add_to_removal_list)
        self.add_to_removal_stack = True
        self._update_history()
    def get_markup(self) -> IKMarkup:
        return IKMarkup([[IKButton('بستن', callback_data=Callback.MESSAGE_CLEANUP)]])

class PronunciationPost(GhostPost):
    def __init__(self, update: Update, word: str, lesson_id):
        super().__init__(update)
        self.word = word
        self.vocab = globals.lessons.get_by_id(lesson_id).vocab
        # print(self.word, self.vocab)
        assert self.vocab is not None
        self.edit = False
    def get_content(self) -> Content:
        # Finding the original word without endings(ing, ed, etc.)
        original_word = None
        for vocab_word in self.vocab:
            if self.word.startswith(vocab_word):
                original_word = vocab_word
                break
        assert original_word is not None
        translation = globals.defs.translate(original_word)

        text = '<b>{}</b>\n{}'.format(original_word, '\n'.join(translation))

        data=Synthesis(f'{original_word}\n{original_word}', speed=80)
        
        return Content(file=data, text=text, type=Content.Type.VOICE)
    

class NarrationPost(GhostPost):
    def __init__(self, update: Update, lesson_id):
        super().__init__(update)
        self.lesson_id = lesson_id
        self.edit = False
    def get_content(self) -> Content:
        lesson = globals.lessons.get_by_id(self.lesson_id)
        speed = 100
        if lesson.grade <= 3: 
            speed = 85
        return Content(file=Synthesis(lesson.text, 0, speed), type=Content.Type.VOICE)

class PageContainerPost(Post):
    """
    Abstract base class for posts that support navigation between several "pages". 
    """
    def __init__(self, update: Update, num_pages):
        super().__init__(update)
        self.num_pages = num_pages
        self.page_idx = 0
        self._update_history()
        #don't override previous post, should be able to return to it
        # globals.history.make_navigational_post(self, self.update)
    def go_back(self) -> Post:
        return globals.history.get_navigational_post(self.owner_id).get_first(self.type, False).post
    def get_next_post(self) -> Post:
        self.page_idx += 1
        self._update_history()
        return self
    def get_previous_post(self) -> Post:
        self.page_idx -= 1
        return globals.history.get_navigational_post(self.owner_id).previous().post
    def get_markup(self) -> IKMarkup:
        navigation_buttons: List[IKButton] = []

        if self.page_idx > 0:
            navigation_buttons.append(
                IKButton('قبلی', callback_data=Callback.PREVIOUS))
        if self.page_idx < self.num_pages - 1:
            navigation_buttons.append(
                IKButton('بعدی', callback_data=Callback.NEXT))

        return IKMarkup([navigation_buttons, [IKButton('بازگشت', callback_data=Callback.BACK)]])

class ChooseLessonPost(PageContainerPost):
    def __init__(self, update: Update):
        num_pages = int(globals.lessons.len / LESSONS_PER_PAGE)
        self.lessons_per_page = LESSONS_PER_PAGE
        super().__init__(update, num_pages)
    def get_content(self):
        return Content(text='Please choose one of the following:')
    def get_markup(self):
        buttons = []
        for i in range(self.lessons_per_page):
            lesson_id = self.page_idx * self.lessons_per_page + i
            buttons.append([IKButton(
                globals.lessons.get_by_id(index=lesson_id).name,
                callback_data=Callback.BASE_LESSON_STRING+str(lesson_id))])
        return IKMarkup(buttons + super().get_markup().inline_keyboard)


class PronunciationQuizPost(PageContainerPost):
    def __init__(self, update: Update, lesson_id):
        self.vocab = globals.lessons.get_by_id(lesson_id).vocab
        assert self.vocab is not None
        super().__init__(update, len(self.vocab))

        self.lesson_id = lesson_id
    def get_content(self) -> Content:
        return Content(text='Please pronounce the following word 2 times:\n* ' +
                       globals.lessons.get_by_id(self.lesson_id).vocab[self.page_idx])

#FIX: can't test this, so not fixing atm
class PronunciationResponsePost(GhostPost, BackSupportPost):
    def __init__(self, update: Update, lesson_id, word_num, results):
        super().__init__(update)
        self.vocab = globals.lessons.get_by_id(lesson_id).vocab
        assert self.vocab is not None
        self.lesson_id = lesson_id
        self.word_num = word_num
        self.results = results
        self.questions_remaining = word_num < len(self.vocab) - 1

    def get_content(self) -> Content:
        msg = self.results

        if not self.questions_remaining:
            msg += '\n\n Well done! You finished the test.'

        return Content(text=msg)

    def get_markup(self) -> IKMarkup:
        button_row = []
        if self.questions_remaining:
            button_row.append(IKButton('خب', callback_data=Callback.NEXT_QUIZ_QUESTION))

        button_row.append(IKButton('دوباره', callback_data=Callback.PRONUNCIATION_QUIZ))
        
        return IKMarkup([button_row] + super().get_markup().inline_keyboard)


