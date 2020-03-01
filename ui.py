from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, ReplyKeyboardRemove
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List
from lessons import Lesson
from synthesis import synthesis
class Constants():
    NumOfLessonsInEachPage = 5

class Callback():
    HOME = 'HOME'
    PLACEMENT_TEST = 'PLACEMENT_TEST'
    REVIEW_WORDS = 'REVIEW_WORDS'
    CHOOSE_LESSON = 'CHOOSE_LESSON'

    # The lesson index is appended to base string here:
    BASE_LESSON_STRING = 'LESSON_'
    NEXT_LESSON_PAGE = "NEXT_LESSON_PAGE"
    PREV_LESSON_PAGE = "PREV_LESSON_PAGE"
    SEARCH_LESSONS_BY_GRADE = "SEARCH_LESSONS_BY_GRADE"
    SEARCH_LESSONS_BY_NAME = "SEARCH_LESSONS_BY_NAME"
    NARRATION = 'NARRATION'
    PRONUNCIATION_QUIZ = 'PRONUNCIATION_QUIZ'
    CLOZE_TEST = 'CLOZE_TEST'


class Content():
    class FileType(Enum):
        TEXT = auto()
        VOICE = auto()
        PHOTO = auto()

    def __init__(self, text=None, file_dir=None, file_type=FileType.TEXT):
        self.text = text
        self.file_dir = file_dir
        self.file_type = file_type

class Post(ABC):
    def __init__(self):
        self.parse_mode = 'html'

    @abstractmethod
    def get_content(self) -> Content:
        pass

    def get_markup(self):
        return None

class HomePost(Post):
    def __init__(self):
        super().__init__()

    def get_content(self):
        return Content(text='سلام. به روبات آموزش زبان خوش آمدید! برای شروع لطفاً یکی از موارد زیر را انتخاب کنید')

    def get_markup(self):
        return IKM([[IKB('آزمون تعیین سطح', callback_data=Callback.PLACEMENT_TEST)],
                    [IKB('درس‌ها', callback_data=Callback.CHOOSE_LESSON)],
                    [IKB('لغات ستاره‌دار', callback_data=Callback.REVIEW_WORDS)]])


class ChooseLessonPost(Post):
    def __init__(self, lessons = List[Lesson]):
        super().__init__()
        self.lessons = lessons
        self.offset = 0

    def get_content(self):
        return Content(text=f'یکی از متون زیر را انتخال کنید\n{self.offset + 1}-{self.offset + 1 + Constants.NumOfLessonsInEachPage}')

    def get_markup(self):
        button_list = []
        for i in range(Constants.NumOfLessonsInEachPage):
            pick = i + self.offset
            button_list.append(
                [IKB(self.lessons[pick].name, callback_data=Callback.BASE_LESSON_STRING + self.lessons[pick].index)])
        button_list.append([IKB('صفحه قبل', callback_data=Callback.PREV_LESSON_PAGE), IKB('صفحه بعد', callback_data=Callback.NEXT_LESSON_PAGE)])
        button_list.append([IKB('بازگشت', callback_data=Callback.HOME)])
        return IKM(button_list)
    def go_next_page(self):
        self.offset += Constants.NumOfLessonsInEachPage
        if self.offset + Constants.NumOfLessonsInEachPage > len(self.lessons):
            self.offset = 0
        return self
    def go_prev_page(self):
        if self.offset >= Constants.NumOfLessonsInEachPage:
            self.offset -= Constants.NumOfLessonsInEachPage
        elif self.offset < Constants.NumOfLessonsInEachPage: 
            self.offset = len(self.lessons) - Constants.NumOfLessonsInEachPage
        return self
    def search_by_name(self):
        pass
    def search_by_grade(self):
        pass


class LessonPost(Post):
    def __init__(self, lesson: Lesson):
        super().__init__()
        self.lesson = lesson
        self.vocab_available = False
        self.cloze_available = False
        if lesson.vocab:
            self.vocab_available = True
        if lesson.cloze:
            self.cloze_available = True

    def get_content(self):
        text = "<b>{}</b>\n\n{}".format(
            lesson.name, lesson.text)
        return Content(text=text)

    def get_markup(self):
        markupList =    [[IKB('Listen to Narration (takes time)', callback_data=Callback.NARRATION)]]
        if self.cloze_available:
            markupList.append(
                        [IKB('Cloze Test', callback_data=Callback.CLOZE_TEST)])
        if self.vocab_available:
            markupList.append( 
                        [IKB('Vocabulary Quiz', callback_data=Callback.VOCABULARY_QUIZ)])
        markupList.append(
                        [IKB('بازگشت', callback_data=Callback.CHOOSE_LESSON)]
        )
        return IKM(markupList)

class NarrationPost(Post):
    def __init__(self, lesson: Lesson):
        super().__init__()
        self.lesson = lesson

    def get_content(self):
        return Content(file_dir=synthesis(self.lesson.text, 1), file_type=Content.FileType.VOICE)


class VocabQuizPost(Post):
    def __init__(self, lesson: Lesson, wordIndex: int):
        super().__init__()
        self.lesson = lesson
        self.wordIndex = wordIndex
    def get_content(self):
        return Content(text='Please pronounce the following word 2 times:\n* ' + lesson.vocab[wordIndex])
    def get_markup(self):
        return IKM([[IKB('بازگشت', callback_data=Callback.BASE_LESSON_STRING + lesson.index)]])


class VocabResponsePost(Post):
    def __init__(self, lesson: Lesson, wordIndex: int, recognitionOutput: str, byOrder=True):
        super().__init__()
        self.lesson = lesson
        self.wordIndex = wordIndex
        self.recognitionOutput = recognitionOutput
        self.byOrder = byOrder
        self.questions_remaining = -1
        if byOrder:
            self.questions_remaining = len(lesson.vocab) - wordIndex
    def get_content(self):
        description = 'Voice received in response to word: "{}"'.format(
            lesson.vocab[self.wordIndex])
        if self.recognitionOutput == self.lesson.vocab[wordIndex]:
            result = True
        else:
            result = False
        msg = '{}\n\nprocessed:\n{}\n\nresult: {}\n\n'.format(
            description, self.output, result)
        if self.byOrder:
            msg += f"Remaining: {self.questions_remaining}"
            self.questions_remaining -= 1
        if self.questions_remaining == 0:
            msg += '\n\n Well done! You finished the test.'

        return Content(text=msg)

    def get_markup(self):
        if self.questions_remaining > 0:
            return IKM([[IKB('بعدی', callback_data=Callback.PRONUNCIATION_QUIZ)],
                        [IKB('بازگشت', callback_data=Callback.BASE_LESSON_STRING + self.lesson.index)]])
        else:
            return IKM([[IKB('بازگشت', callback_data=Callback.BASE_LESSON_STRING + self.lesson.index)]])


class UnimplementedResponsePost(Post):
    def __init__(self):
        super().__init__()

    def get_content(self):
        return Content(text="Sry don't know how to respond to that!")

    def get_markup(self):
        return IKM([[IKB('بازگشت', callback_data=Callback.HOME)]])
