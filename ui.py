from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, ReplyKeyboardRemove
from enum import Enum
from lessons import parse_lessons, Lesson


class Interface():
    CALLBACK_HOME = '-1'
    CALLBACK_PLACEMENT_TEST = '0'
    CALLBACK_REVIEW_WORDS = '2'
    CALLBACK_CHOOSE_LESSON = '3'
    CALLBACK_LESSON_NUM = '4'
    CALLBACK_PRONUNCIATION_QUIZ = '5'

    home_text = 'سلام. به روبات آموزش زبان خوش آمدید! برای شروع لطفاً یکی از موارد زیر را انتخاب کنید'
    home_markup = IKM([[IKB('آزمون تعیین سطح', callback_data=CALLBACK_PLACEMENT_TEST)],
                       [IKB('درس‌ها', callback_data=CALLBACK_CHOOSE_LESSON)],
                       [IKB('لغات ستاره‌دار', callback_data=CALLBACK_REVIEW_WORDS)]])

    num_lessons = 5
    lessons = parse_lessons()

    choose_lesson_text = 'Please choose one of the following:'

    button_list = []
    for i in range(num_lessons):
        button_list.append(
            [IKB(lessons[i].name, callback_data=CALLBACK_LESSON_NUM+str(i))])

    button_list.append([IKB('بازگشت', callback_data=CALLBACK_HOME)])
    choose_lesson_markup = IKM(button_list)

    def lesson_text(lesson_num, lessons=lessons):
        return "<b>{}</b>\n\n{}".format(lessons[lesson_num].name, lessons[lesson_num].text)

    lesson_markup = IKM([[IKB('Pronunciation Quiz', callback_data=CALLBACK_PRONUNCIATION_QUIZ)],
                         [IKB('بازگشت', callback_data=CALLBACK_CHOOSE_LESSON)]])

    pronunciation_quiz_not_available = 'No quiz available for this lesson.'

    def pronunciation_quiz_text(lesson_num, word_num, lessons=lessons):
        return 'Please pronounce the following word twice:\n* ' + lessons[lesson_num].vocab[word_num]

    def pronunciation_quiz_markup(lesson_num, CALLBACK_LESSON_NUM=CALLBACK_LESSON_NUM):
        return IKM([[IKB('بازگشت', callback_data=CALLBACK_LESSON_NUM+str(lesson_num
                                                                         ))]])

    def pronunciation_response_text(lesson_num, word_num, lessons=lessons):
        return 'Voice received in response to word: "{}"'.format(lessons[lesson_num].vocab[word_num])

    def pronunciation_response_markup(lesson_num, CALLBACK_PRONUNCIATION_QUIZ=CALLBACK_PRONUNCIATION_QUIZ, CALLBACK_LESSON_NUM=CALLBACK_LESSON_NUM):
        return IKM([[IKB('بعدی', callback_data=CALLBACK_PRONUNCIATION_QUIZ)],
                    [IKB('بازگشت', callback_data=CALLBACK_LESSON_NUM + str(lesson_num))]])

    def pronunciation_over(lesson_num, CALLBACK_LESSON_NUM=CALLBACK_LESSON_NUM):
        return IKM([[IKB('بازگشت', callback_data=CALLBACK_LESSON_NUM+str(lesson_num))]])
