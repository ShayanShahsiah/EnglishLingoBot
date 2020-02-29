from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, ReplyKeyboardRemove
from enum import Enum
from lessons import parse_lessons, Lesson


class Interface():
    CALLBACK_HOME = '-1'
    CALLBACK_PLACEMENT_TEST = '0'
    CALLBACK_REVIEW_WORDS = '2'
    CALLBACK_CHOOSE_LESSON = '3'
    CALLBACK_LESSON_NUM = '4'
    CALLBACK_RECOGNITION_TEST = '5'

    home_text = 'سلام. به روبات آموزش زبان خوش آمدید! برای شروع لطفاً یکی از موارد زیر را انتخاب کنید'
    home_markup = IKM([[IKB('آزمون تعیین سطح', callback_data=CALLBACK_PLACEMENT_TEST)],
                       [IKB('درس‌ها', callback_data=CALLBACK_CHOOSE_LESSON)],
                       [IKB('لغات ستاره‌دار', callback_data=CALLBACK_REVIEW_WORDS)],
                       [IKB('recognition test', callback_data=CALLBACK_RECOGNITION_TEST)]])

    choose_lesson_text = 'Please choose one of the following:'

    num_lessons = 5
    lessons = parse_lessons()

    button_list = []
    for i in range(num_lessons):
        button_list.append(
            [IKB(lessons[i].name, callback_data=CALLBACK_LESSON_NUM+str(i))])

    button_list.append([IKB('بازگشت', callback_data=CALLBACK_HOME)])
    choose_lesson_markup = IKM(button_list)

    def lesson_text(i, lessons=lessons): return lessons[i].text
    lesson_markup = IKM(
        [[IKB('بازگشت', callback_data=CALLBACK_CHOOSE_LESSON)]])

    def recognition_text(
        i, lessons=lessons): return 'Please pronounce the following word twice:\n* ' + lessons[2].vocab[i]
    recognition_markup = IKM([[IKB('بازگشت', callback_data=CALLBACK_HOME)]])

    def recognition_response_text(
        i, lessons=lessons): return 'Voice received in response to word: "{}"'.format(lessons[2].vocab[i])
    recognition_response_markup = IKM([[IKB('بعدی', callback_data=CALLBACK_RECOGNITION_TEST)],
                                       [IKB('بازگشت', callback_data=CALLBACK_HOME)]])
