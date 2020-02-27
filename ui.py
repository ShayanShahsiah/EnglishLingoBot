from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, ReplyKeyboardRemove
from enum import Enum
from lessons import parse_lessons, Lesson

class Interface():
    CALLBACK_HOME = '-1'
    CALLBACK_PLACEMENT_TEST = '0'
    CALLBACK_REVIEW_WORDS = '2'
    CALLBACK_CHOOSE_LESSON = '3'
    CALLBACK_LESSON_NUM = '4'

    home_text = 'سلام. به روبات آموزش زبان خوش آمدید! برای شروع لطفاً یکی از موارد زیر را انتخاب کنید'
    home_markup = IKM([[IKB('آزمون تعیین سطح', callback_data=CALLBACK_PLACEMENT_TEST)],
    [IKB('درس‌ها', callback_data=CALLBACK_CHOOSE_LESSON)],
    [IKB('لغات ستاره‌دار', callback_data=CALLBACK_REVIEW_WORDS)]])

    choose_lesson_text = 'Please choose one of the following:'

    num_lessons = 5
    lessons = parse_lessons()

    button_list = []
    for i in range(num_lessons):
        button_list.append([IKB(lessons[i].name, callback_data=CALLBACK_LESSON_NUM+str(i))])

    button_list.append([IKB('بازگشت', callback_data=CALLBACK_HOME)])
    choose_lesson_markup = IKM(button_list)

    lesson_text = lambda i, lessons=lessons: lessons[i].text
    lesson_markup = IKM([[IKB('بازگشت', callback_data=CALLBACK_CHOOSE_LESSON)]])