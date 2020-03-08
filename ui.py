from telegram import InlineKeyboardMarkup as IKMarkup, InlineKeyboardButton as IKButton
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Optional, Callable, Union
import ast
import copy
from lessons import Lessons
from definitions import Definitions
from synthesis import synthesis

DISPLAYED_LESSONS = 30
LESSONS_PER_PAGE = 6

# Really tried to make this a "static" variable in Post; but weird things happened :|
#TODO: put in database
navigation_stack = []

defs: Definitions = Definitions()

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

class Post(ABC):
    """
    Abstract base class for all posts.
    """

    def __init__(self):
        self._update_stack()
        self.parse_mode: str = 'html'

    def _update_stack(self):
        # For a base Post (not BackSupportPost), previous Posts are discarded.
        global navigation_stack
        navigation_stack = [self]
        print('This got called :/')

    @abstractmethod
    def get_content(self) -> Content:
        pass

    def get_markup(self) -> IKMarkup:
        return IKMarkup([[]])


class BackSupportPost(Post):
    """
    Abstract base class for posts that support navigation to the previous post.
    """
    def __init__(self):
        super().__init__()

    def _update_stack(self):
        # For a BackSupportPost, previous Posts are kept; since they can be returned to.
        global navigation_stack
        navigation_stack.append(self)

    def get_previous_post(self) -> Post:
        global navigation_stack
        if navigation_stack[-1] is self:
            navigation_stack.pop()

        # Returns the last Post in the stack:
        return navigation_stack[-1]

    def get_markup(self) -> IKMarkup:
        return IKMarkup([[IKButton('بازگشت', callback_data=Callback.BACK)]] +
                        super().get_markup().inline_keyboard)


class PageContainerPost(Post):
    """
    Abstract base class for posts that support navigation between several "pages". 
    """
    def __init__(self, num_pages):
        super().__init__()
        self.num_pages = num_pages
        self.page_idx = 0

    def go_next(self):
        self.page_idx += 1

    def go_previous(self):
        self.page_idx -= 1

    def get_markup(self) -> IKMarkup:
        navigation_buttons: List[IKButton] = []

        if self.page_idx > 0:
            navigation_buttons.append(
                IKButton('قبلی', callback_data=Callback.PREVIOUS))
        if self.page_idx < self.num_pages - 1:
            navigation_buttons.append(
                IKButton('بعدی', callback_data=Callback.NEXT))

        return IKMarkup([navigation_buttons] + super().get_markup().inline_keyboard)


class GhostPost(Post):
    """
    Abstract base class for posts that are outside the back navigation stack.

    Could for example be used for a short message sent after a bigger "main" message
    without affecting the "back button" functionality of the older message.
    """
    def _update_stack(self):
        # Doesn't affect the stack at all
        pass

class HomePost(Post):
    def __init__(self):
        super().__init__()

    def get_content(self):
        return Content(text='سلام. به روبات آموزش زبان خوش آمدید! برای شروع لطفاً یکی از موارد زیر را انتخاب کنید')

    def get_markup(self):
        return IKMarkup([
            [IKButton('آزمون تعیین سطح', callback_data=Callback.PLACEMENT_TEST)],
            [IKButton('درس‌ها', callback_data=Callback.CHOOSE_LESSON_POST)],
            [IKButton('لغات ستاره‌دار', callback_data=Callback.REVIEW_WORDS)]])


class ChooseLessonPost(PageContainerPost, BackSupportPost):
    def __init__(self):
        super().__init__(num_pages=DISPLAYED_LESSONS)
        self.lessons_per_page = LESSONS_PER_PAGE

    def get_content(self):
        return Content(text='Please choose one of the following:')

    def get_markup(self):
        buttons = []
        for i in range(self.lessons_per_page):
            lesson_id = self.page_idx * self.lessons_per_page + i
            buttons.append([IKButton(
                Lessons.get_by_id(lesson_id).name,
                callback_data=Callback.BASE_LESSON_STRING+str(lesson_id))])

        return IKMarkup(buttons + super().get_markup().inline_keyboard)


class LessonPost(BackSupportPost):
    def __init__(self, lesson_id):
        super().__init__()
        self.lesson_id = lesson_id
        self.vocab = ast.literal_eval(Lessons.get_by_id(self.lesson_id).vocab)
        self.vocab_available = self.vocab is not None
        self.text = self._slashify()

    def _slashify(self) -> str:
        text = Lessons.get_by_id(self.lesson_id).text
        self.vocab = ast.literal_eval(Lessons.get_by_id(self.lesson_id).vocab)
        if self.vocab is None:
            return text
        
        words: List[str] = text.split()
        for i in range(len(words)):
            matched = False
            for j in range(len(self.vocab)):
                if self.vocab[j] != '' and words[i].startswith(self.vocab[j]):
                    matched = True
                    self.vocab[j] = ''
                    break
            if matched:
                words[i] = '/' + words[i]

        return ' '.join(words)

    def get_content(self) -> Content:
        text = "<b>{}</b>\n\n{}".format(
            Lessons.get_by_id(self.lesson_id).name, self.text)
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


class PronunciationPost(GhostPost):
    def __init__(self, word: str, lesson_id):
        super().__init__()
        self.word = word
        self.vocab = ast.literal_eval(Lessons.get_by_id(lesson_id).vocab)
        print(self.word, self.vocab)
        assert self.vocab is not None

    def get_content(self) -> Content:
        # Finding the original word without endings(ing, ed, etc.)
        original_word = None
        for vocab_word in self.vocab:
            if self.word.startswith(vocab_word):
                original_word = vocab_word
                break
        assert original_word is not None
        translation = defs.translate(original_word)

        text = '<b>{}</b>\n{}'.format(original_word, '\n'.join(translation))

        data=synthesis(f'{original_word}\n{original_word}', speed=80)
        
        return Content(file=data, text=text, type=Content.Type.VOICE)

class NarrationPost(GhostPost):
    def __init__(self, lesson_id):
        super().__init__()
        self.lesson_id = lesson_id

    def get_content(self) -> Content:
        lesson = Lessons.get_by_id(self.lesson_id)
        speed = 100
        if lesson.grade <= 5: 
            speed = 85
        return Content(file=synthesis(lesson.text, 0, speed), type=Content.Type.VOICE)


class PronunciationQuizPost(PageContainerPost, BackSupportPost):
    def __init__(self, lesson_id):
        self.vocab = ast.literal_eval(Lessons.get_by_id(lesson_id).vocab)
        assert self.vocab is not None
        super().__init__(len(self.vocab))

        self.lesson_id = lesson_id

    def get_content(self) -> Content:
        return Content(text='Please pronounce the following word 2 times:\n* ' +
                       self.vocab[self.page_idx])


class PronunciationResponsePost(GhostPost, BackSupportPost):
    def __init__(self, lesson_id, word_num, results):
        self.vocab = ast.literal_eval(Lessons.get_by_id(lesson_id).vocab)
        assert self.vocab is not None

        super().__init__()

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


class UnimplementedResponsePost(BackSupportPost):
    def __init__(self, text="Sry don't know how to respond to that!"):
        super().__init__()
        self.text = text

    def get_content(self):
        return Content(text=self.text)
