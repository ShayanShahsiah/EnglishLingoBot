from typing import List
from os.path import join
from functools import wraps
from fileHandler import Files
from typing import List
import random
import json
import requests


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
        self.contents: dict() = LessonDict
        self.vocab: list = None
        self.cloze: Cloze = None
        if "vocab" in LessonDict:
            self.vocab = LessonDict["vocab"]
        if "cloze" in LessonDict:
            self.cloze = Cloze(LessonDict["cloze"])

    def __str__(self):
        return str(self.contents)

    def __repr__(self):
        return str(self.contents)


class Lessons():
    instantated = False

    def __init__(self):
        if not self.instantated:
            with open(Files.TextDataJson, 'r') as f:
                self.allLessons: dict = json.load(f)
        self.instantated = True

    def getNRandom(self, hasVocab=True, hasCloze=True, count=1) -> List[Lesson]:
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

    def getAll(self, hasCloze=True, hasVocab=True, sort=True, reversed=False) -> List[Lesson]:
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
            if sort:
                all = sorted(all, key=lambda k: k['grade'], reverse=reversed)
            all.append(Lesson(lesson))
        return all

    def getByGrade(self, minGrade, maxGrade, hasCloze=True, hasVocab=True) -> List[Lesson]:
        """
        also sorts w/ descending order
        """
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


if __name__ == "__main__":
    test = Lessons()
    a = test.getRandom().cloze.text
    print(a)
