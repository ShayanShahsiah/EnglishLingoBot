from typing import List, Optional
from fileHandler import Files
from typing import List, Optional
import random
import json


class Cloze:
    def __init__(self, text, answers):
        self.text: str = text
        self.answers: List[str] = answers

    @staticmethod
    # Have to put type hint in quotes because the class isn't defined yet
    def from_dict(cloze_dict: dict) -> 'Cloze':
        return Cloze(cloze_dict['text'], cloze_dict['answers'])

    def __repr__(self):
        return f'Cloze(text={self.text}, answers={self.answers})'


class Lesson:
    def __init__(self, name, grade, text, vocab, cloze, index):
        self.name: str = name
        self.grade: int = grade
        self.text: str = text
        self.vocab: Optional[List[str]] = vocab
        self.cloze: Optional[Cloze] = cloze
        self.index: int = index

    @staticmethod
    # Have to put type hint in quotes because the class isn't defined yet
    def from_dict(dict: dict) -> 'Lesson':
        name, grade, text, index = dict['name'], dict['grade'], dict['text'], dict['index']
        vocab = dict.get('vocab', None)

        cloze: Optional[Cloze] = None
        if 'cloze' in dict:
            cloze = Cloze.from_dict(dict['cloze'])

        return Lesson(name=name, grade=grade, text=text, vocab=vocab, cloze=cloze, index=index)

    def __repr__(self):
        return 'Lesson(name={}, grade={}, text={}, vocab={}, cloze={}, index={})'.format(
            repr(self.name), repr(self.grade), repr(self.text), repr(self.vocab), repr(self.cloze), repr(self.index))

    def __str__(self):
        if len(self.name) < 15:
            name_str = self.name
        else:
            name_str = self.name[:15] + '... '

        text_str = self.text[:15] + '... '

        if self.vocab:
            vocab_str = '[...]'
        else:
            vocab_str = 'None'

        if self.cloze:
            cloze_str = 'Cloze(...)'
        else:
            cloze_str = 'None'

        return 'Lesson(name: {}, grade: {}, text: {}, vocab: {}, cloze: {}, index: {})'.format(
            name_str, self.grade, text_str, vocab_str, cloze_str, self.index)


class Lessons():
    def __init__(self):
        with open(Files.TextDataJson, 'r') as f:
            self._lesson_dicts: list = json.load(f)

        # TODO: reverse lessons in json instead of dynamically
        self._lesson_dicts.reverse()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        del self._lesson_dicts

    def get_all(self, count=None, vocab_needed=True, cloze_needed=True,
                    min_grade=None, max_grade=None, shuffle=False, reverse=False) -> List[Lesson]:

        if count is None:
            count = len(self._lesson_dicts)

        filtered_lessons: List[Lesson] = []
        for lesson_dict in self._lesson_dicts:
            lesson: Lesson = Lesson.from_dict(lesson_dict)

            vocab_requirement = not (vocab_needed and lesson.cloze is None)
            cloze_requirement = not (cloze_needed and lesson.cloze is None)

            grade_min_requirement = min_grade is None or lesson.grade >= min_grade
            grade_max_requirement = max_grade is None or lesson.grade <= max_grade

            if vocab_requirement and cloze_requirement and grade_min_requirement and grade_max_requirement:
                filtered_lessons.append(lesson)

        if shuffle:
            return random.sample(filtered_lessons, k=count)
        elif reverse:
            return filtered_lessons[:count][::-1]
        else:
            return filtered_lessons[:count]

    def get_one(self, vocab_needed=True, cloze_needed=True, min_grade=None, max_grade=None) -> Lesson:
        return self.get_all(count=1, vocab_needed=vocab_needed, cloze_needed=cloze_needed, min_grade=min_grade, max_grade=max_grade)[0]

    def get_by_id(self, index: int) -> Lesson:
        return Lesson.from_dict(self._lesson_dicts[index])


if __name__ == "__main__":
    with Lessons() as test:
        a = test.get_all(vocab_needed=False, cloze_needed=False, max_grade=0.2)
        #a = test.get_by_id(-1)

    #print(a)
    for e in a:
        print(e)