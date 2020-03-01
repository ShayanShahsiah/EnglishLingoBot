from typing import List
from os.path import join
from functools import wraps
from fileHandler import Files
from typing import List
import random
import json
import requests

class Vocabulary():
    def __init__(self, wordList: list):
        self._list = wordList
        self.word = self._list[0]
        self.index = 0
        self.len = len(self._list)
    def next(self):
        self.word = self._list[index]
        self.index += 1
        if self.index == self.len:
            return None
        return self
class Cloze():
    def __init__(self, clozeDict: dict):
        self.text: str = clozeDict["text"]
        self.answers: list = clozeDict["answers"]
        self.contents: dict() = clozeDict

    def __str__(self):
        return str(self.contents)

    def __repr__(self):
        return str(self.contents)


class Lesson():
    def __init__(self, LessonDict: dict):
        self.name: str = LessonDict["name"]
        self.grade: int = LessonDict["grade"]
        self.text: str = LessonDict["text"]
        self.index: int = LessonDict["index"]
        self.contents: dict() = LessonDict
        self.vocab: Vocabulary = None
        self.cloze: Cloze = None
        if "vocab" in LessonDict:
            self.vocab = Vocabulary(LessonDict["vocab"])
        if "cloze" in LessonDict:
            self.cloze = Cloze(LessonDict["cloze"])

    def __str__(self):
        return str(self.contents)

    def __repr__(self):
        return str(self.contents)


class Lessons():
    def __init__(self):
        self.instantated = False
        self.__load()
    def __load(self):
        if self.instantated:
            return
        with open(Files.TextDataJson, 'r') as f:
            self.allLessons: list = json.load(f)
        self.instantated = True
    def __enter__(self):
        self.instantated = False
        self.__load()
        return self
    def __exit__(self, type, value, traceback):
        del self.allLessons
        self.instantated = False
    def getNRandom(self, hasVocab=True, hasCloze=True, count=1) -> List[Lesson]:
        self.__load()
        pickList = list()
        for each in self.allLessons:
            if hasVocab:
                if not "vocab" in each:
                    continue
            else:
                if "vocab" in each:
                    continue
            if hasCloze:
                if not "cloze" in each:
                    continue
            else:
                if "cloze" in each:
                    continue
            pickList.append(each)
        try:
            lesson = random.sample(pickList, k=count)
        except IndexError:
            #no result
            return None
        return [Lesson(i) for i in lesson]

    def getRandom(self, hasVocab=True, hasCloze=True,) -> Lesson:
        self.__load()
        pickList = list()
        for each in self.allLessons:
            if hasVocab:
                if not "vocab" in each:
                    continue
            else:
                if "vocab" in each:
                    continue
            if hasCloze:
                if not "cloze" in each:
                    continue
            else:
                if "cloze" in each:
                    continue
            pickList.append(each)
        try:
            lesson = random.choice(pickList)
        except IndexError:
            #no result
            return None
        return Lesson(lesson)

    def getAll(self, hasCloze=True, hasVocab=True, randomized=False, sorted=True, reversed=False) -> List[Lesson]:
        self.__load()
        all = list()
        for lesson in self.allLessons:
            if hasVocab:
                if not "vocab" in lesson:
                    continue
            else:
                if "vocab" in lesson:
                    continue
            if hasCloze:
                if not "cloze" in lesson:
                    continue
            else:
                if "cloze" in lesson:
                    continue
            if sorted:
                all = sorted(all, key=lambda k: k['grade'], reverse=reversed)
            elif randomized:
                all = random.shuffle(all)
            all.append(Lesson(lesson))
        return all

    def getByGrade(self, minGrade, maxGrade, hasCloze=True, hasVocab=True) -> List[Lesson]:
        """
        also sorts w/ descending order
        """
        self.__load()
        all = list()
        for lesson in self.allLessons:
            if hasVocab:
                if not "vocab" in lesson:
                    continue
            else:
                if "vocab" in lesson:
                    continue
            if hasCloze:
                if not "cloze" in lesson:
                    continue
            else:
                if "cloze" in lesson:
                    continue
            if lesson["grade"] >= minGrade and lesson["grade"] <= maxGrade:
                all.append(lesson)
        all = sorted(all, key=lambda k: k['grade'], reverse=True)
        ret = list()
        for one in all:
            ret.append(Lesson(one))
        return ret
    def getByID(self, index: int) -> Lesson:
        self.__load()
        return Lesson(self.allLessons[-index-1])

if __name__ == "__main__":
    with Lessons() as test:
        a = test.getByID(20)
    print(a.text)
