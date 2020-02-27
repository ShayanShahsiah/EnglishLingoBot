from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, ReplyKeyboardRemove
from enum import Enum

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

    def _create_choose_lesson_markup(num, callback_lesson_num, callback_home):
        button_list = []
        for i in range(num):
            button_list.append([IKB(f'lesson {i+1}', callback_data=callback_lesson_num+str(i))])

        button_list.append([IKB('بازگشت', callback_data=callback_home)])
        return IKM(button_list)
    
    choose_lesson_markup = _create_choose_lesson_markup(num_lessons, CALLBACK_LESSON_NUM, CALLBACK_HOME)

    lesson_text = "Here's a sample text!"
    lesson_markup = IKM([[IKB('بازگشت', callback_data=CALLBACK_CHOOSE_LESSON)]])