from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Optional, Callable, Union
import ast

from telegram import InlineKeyboardMarkup as IKMarkup, InlineKeyboardButton as IKButton, Update

from lessons import Lessons
from synthesis import synthesis
from ui_lib import Callback as LibCallback, Content, Post, BasicPost, BackSupportPost, PageContainerPost, GhostPost
import global_vars

DISPLAYED_LESSONS = 30
LESSONS_PER_PAGE = 6


class Callback(LibCallback):
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


class LessonPost(BackSupportPost):
    def __init__(self, update: Update, lesson_id):
        self.lesson_id = lesson_id
        self.vocab = ast.literal_eval(Lessons.get_by_id(self.lesson_id).vocab)
        self.vocab_available = self.vocab is not None
        self.text = self._slashify()
        super().__init__(update)

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


class UnimplementedResponsePost(BackSupportPost):
    def __init__(self, update, text="Sry don't know how to respond to that!"):
        self.text = text
        super().__init__(update)

    def get_content(self):
        return Content(text=self.text)


class PronunciationPost(GhostPost):
    def __init__(self, update: Update, word: str, lesson_id):
        super().__init__(update)
        self.word = word
        self.vocab = ast.literal_eval(Lessons.get_by_id(lesson_id).vocab)
        print(self.word, self.vocab)
        assert self.vocab is not None
        # print(self.word, self.vocab)
        self.getSynthesis()

    def getSynthesis(self):
        # Finding the original word without endings(ing, ed, etc.)
        original_word = None
        for vocab_word in reversed(self.vocab):
            if self.word.startswith(vocab_word):
                original_word = vocab_word
                break
        assert original_word is not None
        translation = global_vars.defs.translate(original_word)

        self.text = '<b>{}</b>\n{}'.format(original_word,
                                           '\n'.join(translation))

        self.data = synthesis(f'{original_word}\n{original_word}', speed=80)

    def get_content(self) -> Content:
        return Content(file=self.data, text=self.text, type=Content.Type.VOICE)


class NarrationPost(GhostPost):
    def __init__(self, update: Update, lesson_id):
        super().__init__(update)
        self.lesson_id = lesson_id
        self.getSynthesis()

    def getSynthesis(self):
        lesson = Lessons.get_by_id(self.lesson_id)
        speed = 100
        if lesson.grade <= 3:
            speed = 85
        self.data = synthesis(lesson.text, 0, speed)

    def get_content(self) -> Content:
        return Content(file=self.data, type=Content.Type.VOICE)


class ChooseLessonPost(PageContainerPost):
    def __init__(self, update: Update):
        num_pages = Lessons.get_count() // LESSONS_PER_PAGE
        self.lessons_per_page = LESSONS_PER_PAGE
        super().__init__(update, num_pages)

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


class PronunciationQuizPost(PageContainerPost):
    def __init__(self, update: Update, lesson_id):
        self.vocab = ast.literal_eval(Lessons.get_by_id(lesson_id).vocab)
        assert self.vocab is not None
        super().__init__(update, len(self.vocab))

        self.lesson_id = lesson_id

    def get_content(self) -> Content:
        return Content(text='Please pronounce the following word 2 times:\n* ' +
                       self.vocab[self.page_idx])


# FIX: can't test this, so not fixing atm
class PronunciationResponsePost(GhostPost, BackSupportPost):
    def __init__(self, update, lesson_id, word_num, results):
        super().__init__(update)
        self.vocab = ast.literal_eval(Lessons.get_by_id(lesson_id).vocab)
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
            button_row.append(
                IKButton('خب', callback_data=Callback.NEXT_QUIZ_QUESTION))

        button_row.append(
            IKButton('دوباره', callback_data=Callback.PRONUNCIATION_QUIZ))

        return IKMarkup([button_row] + super().get_markup().inline_keyboard)
