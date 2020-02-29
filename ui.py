from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, ReplyKeyboardRemove
from enum import Enum, auto
from abc import ABC, abstractmethod
from lessons import parse_lessons, Lesson


num_lessons = 5
lessons = parse_lessons()


class Callback():
    HOME = 'HOME'
    PLACEMENT_TEST = 'PLACEMENT_TEST'
    REVIEW_WORDS = 'REVIEW_WORDS'
    CHOOSE_LESSON = 'CHOOSE_LESSON'
    LESSON_NUM = 'LESSON_NUM'
    PRONUNCIATION_QUIZ = 'PRONUNCIATION_QUIZ'


class Message(ABC):
    def __init__(self):
        self.parse_mode = 'html'

    @abstractmethod
    def get_text(self):
        pass

    @abstractmethod
    def get_markup(self):
        pass


class HomeMessage(Message):
    def __init__(self):
        super().__init__()

    def get_text(self):
        return 'سلام. به روبات آموزش زبان خوش آمدید! برای شروع لطفاً یکی از موارد زیر را انتخاب کنید'

    def get_markup(self):
        return IKM([[IKB('آزمون تعیین سطح', callback_data=Callback.PLACEMENT_TEST)],
                    [IKB('درس‌ها', callback_data=Callback.CHOOSE_LESSON)],
                    [IKB('لغات ستاره‌دار', callback_data=Callback.REVIEW_WORDS)]])


class ChooseLessonMessage(Message):
    def __init__(self):
        super().__init__()

    def get_text(self):
        return 'Please choose one of the following:'

    def get_markup(self):
        button_list = []
        for i in range(num_lessons):
            button_list.append(
                [IKB(lessons[i].name, callback_data=Callback.LESSON_NUM+str(i))])
        button_list.append([IKB('بازگشت', callback_data=Callback.HOME)])
        return IKM(button_list)


class LessonMessage(Message):
    def __init__(self, lesson_num):
        super().__init__()
        self.lesson_num = lesson_num
        self.quiz_available = lessons[self.lesson_num].vocab != None

    def get_text(self):
        text = "<b>{}</b>\n\n{}".format(
            lessons[self.lesson_num].name, lessons[self.lesson_num].text)
        if not self.quiz_available:
            text += '\n\n <i>Pronunciation quiz not available for this lesson.</i>'
        return text

    def get_markup(self):
        if self.quiz_available:
            return IKM([[IKB('Pronunciation Quiz', callback_data=Callback.PRONUNCIATION_QUIZ)],
                        [IKB('بازگشت', callback_data=Callback.CHOOSE_LESSON)]])
        else:
            return IKM([[IKB('بازگشت', callback_data=Callback.CHOOSE_LESSON)]])


class PronunciationQuizMessage(Message):
    def __init__(self, lesson_num, word_num):
        super().__init__()
        self.lesson_num = lesson_num
        self.word_num = word_num

    def get_text(self):
        return 'Please pronounce the following word 2 times:\n* ' + lessons[self.lesson_num].vocab[self.word_num]

    def get_markup(self):
        return IKM([[IKB('بازگشت', callback_data=Callback.LESSON_NUM+str(self.lesson_num))]])


class PronunciationResponseMessage(Message):
    def __init__(self, lesson_num, word_num, output, result):
        super().__init__()
        self.lesson_num = lesson_num
        self.word_num = word_num
        self.output = output
        self.result = result
        self.questions_remaining = self.word_num < len(
            lessons[self.lesson_num].vocab) - 1

    def get_text(self):
        description = 'Voice received in response to word: "{}"'.format(
            lessons[self.lesson_num].vocab[self.word_num])

        msg = '{}\n\nprocessed:\n{}\n\nresult: {}'.format(
            description, self.output, self.result)

        if not self.questions_remaining:
            msg += '\n\n Well done! You finished the test.'

        return msg

    def get_markup(self):
        if self.questions_remaining:
            return IKM([[IKB('بعدی', callback_data=Callback.PRONUNCIATION_QUIZ)],
                        [IKB('بازگشت', callback_data=Callback.LESSON_NUM + str(self.lesson_num))]])
        else:
            return IKM([[IKB('بازگشت', callback_data=Callback.LESSON_NUM+str(self.lesson_num))]])


class UnimplementedResponseMessage(Message):
    def __init__(self):
        super().__init__()

    def get_text(self):
        return "Sry don't know how to respond to that!"

    def get_markup(self):
        return None
