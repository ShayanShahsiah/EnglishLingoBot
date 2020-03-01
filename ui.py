from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, ReplyKeyboardRemove
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List
from lessons import parse_lessons, Lesson
import audio

num_lessons = 5
lessons: List[Lesson] = parse_lessons()


class Callback():
    HOME = 'HOME'
    PLACEMENT_TEST = 'PLACEMENT_TEST'
    REVIEW_WORDS = 'REVIEW_WORDS'
    CHOOSE_LESSON = 'CHOOSE_LESSON'

    # The lesson number is added after 'LESSON_NUM' before callback.
    # TODO: Probably need a better mechanism to carry lesson number information.
    LESSON_NUM = 'LESSON_NUM'

    NARRATION = 'NARRATION'
    PRONUNCIATION_QUIZ = 'PRONUNCIATION_QUIZ'


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
    def __init__(self):
        super().__init__()

    def get_content(self):
        return Content(text='Please choose one of the following:')

    def get_markup(self):
        button_list = []
        for i in range(num_lessons):
            button_list.append(
                [IKB(lessons[i].name, callback_data=Callback.LESSON_NUM+str(i))])
        button_list.append([IKB('بازگشت', callback_data=Callback.HOME)])
        return IKM(button_list)


class LessonPost(Post):
    def __init__(self, lesson_num):
        super().__init__()
        self.lesson_num = lesson_num
        self.quiz_available = lessons[self.lesson_num].vocab != None

    def get_content(self):
        text = "<b>{}</b>\n\n{}".format(
            lessons[self.lesson_num].name, lessons[self.lesson_num].text)
        if not self.quiz_available:
            text += '\n\n <i>Pronunciation quiz not available for this lesson.</i>'
        return Content(text=text)

    def get_markup(self):
        if self.quiz_available:
            return IKM([[IKB('Listen to Narration', callback_data=Callback.NARRATION)],
                        [IKB('Pronunciation Quiz',
                             callback_data=Callback.PRONUNCIATION_QUIZ)],
                        [IKB('بازگشت', callback_data=Callback.CHOOSE_LESSON)]])
        else:
            return IKM([[IKB('Listen to Narration', callback_data=Callback.NARRATION)],
                        [IKB('بازگشت', callback_data=Callback.CHOOSE_LESSON)]])


class NarrationPost(Post):
    def __init__(self, lesson_num):
        super().__init__()
        self.lesson_num = lesson_num

    def get_content(self):
        if self.lesson_num%2==0:
            speaker = 1
        else:
            speaker = 2
            
        return Content(file_dir=audio.synthesis(lessons[self.lesson_num].text, speaker), file_type=Content.FileType.VOICE)


class PronunciationQuizPost(Post):
    def __init__(self, lesson_num, word_num):
        super().__init__()
        self.lesson_num = lesson_num
        self.word_num = word_num

    def get_content(self):
        return Content(text='Please pronounce the following word 2 times:\n* ' + lessons[self.lesson_num].vocab[self.word_num])

    def get_markup(self):
        return IKM([[IKB('بازگشت', callback_data=Callback.LESSON_NUM+str(self.lesson_num))]])


class PronunciationResponsePost(Post):
    def __init__(self, lesson_num, word_num, output, result):
        super().__init__()
        self.lesson_num = lesson_num
        self.word_num = word_num
        self.output = output
        self.result = result
        self.questions_remaining = self.word_num < len(
            lessons[self.lesson_num].vocab) - 1

    def get_content(self):
        description = 'Voice received in response to word: "{}"'.format(
            lessons[self.lesson_num].vocab[self.word_num])

        msg = '{}\n\nprocessed:\n{}\n\nresult: {}'.format(
            description, self.output, self.result)

        if not self.questions_remaining:
            msg += '\n\n Well done! You finished the test.'

        return Content(text=msg)

    def get_markup(self):
        if self.questions_remaining:
            return IKM([[IKB('بعدی', callback_data=Callback.PRONUNCIATION_QUIZ)],
                        [IKB('بازگشت', callback_data=Callback.LESSON_NUM + str(self.lesson_num))]])
        else:
            return IKM([[IKB('بازگشت', callback_data=Callback.LESSON_NUM+str(self.lesson_num))]])


class UnimplementedResponsePost(Post):
    def __init__(self):
        super().__init__()

    def get_content(self):
        return Content(text="Sry don't know how to respond to that!")

    def get_markup(self):
        return IKM([[IKB('بازگشت', callback_data=Callback.HOME)]])
