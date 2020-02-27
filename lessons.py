from typing import List
import json

class Lesson:
    class Cloze:
        def __init__(self, text: str, answers: List[str]):
                self.text = text
                self.answers = answers

    def __init__(self, name:str, grade: int, text: str, vocab: List[str], cloze: Cloze):
        self.name = name
        self.grade = grade
        self.text = text
        self.vocab = vocab
        self.cloze = cloze
        
#TODO: keeping the whole file in memory is not ideal, might be necessary to use ijson instead
def parse_lessons():
    lessons: List[Lesson] = []
    with open('Data/eslyes.clean.json', 'r') as f:
        print('parsing...')
        lesson_dicts = json.load(f)

    for lesson_dict in lesson_dicts:
        cloze_dict = lesson_dict.get('cloze', None)
        if cloze_dict:
            cloze = Lesson.Cloze(cloze_dict['text'], cloze_dict['answers'])
        else:
            cloze = None
        lesson = Lesson(lesson_dict['name'], lesson_dict['grade'], lesson_dict['text'], lesson_dict.get('vocab', None), cloze)
        lessons.append(lesson)

    return lessons