from typing import List, Optional

from fileHandler import Files
from typing import List, Optional
import random
import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import String, Integer, Column, create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, Query, relationship
from typing import Type

engine = create_engine('sqlite:///test.db', echo=False)

Base: Type = declarative_base()

SessionMaker = sessionmaker(bind=engine)
session: Session = SessionMaker()


class Cloze(Base):
    __tablename__ = 'clozes'

    cloze_id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    answers = Column(String, nullable=False)
    lesson = relationship("Lesson", uselist=False, back_populates="cloze")

    def __repr__(self):
        return f'Cloze(text={self.text}, answers={self.answers})'


class Lesson(Base):
    __tablename__ = 'lessons'

    lesson_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    grade = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    vocab = Column(String, nullable=True)
    cloze_id = Column(Integer, ForeignKey('clozes.cloze_id'), nullable=True)
    cloze = relationship("Cloze", uselist=False, back_populates="lesson")

    def __repr__(self):
        return "Lesson(id={}, name='{}...', grade={})".format(
            self.lesson_id, self.name[:15], self.grade)


class Lessons:
    @staticmethod
    def get_all(min_grade=0, max_grade=12, count: Optional[int] = None, shuffle=False) -> 'List[Lesson]':

        query: Query = session.query(Lesson).filter(
            Lesson.grade >= min_grade, Lesson.grade < max_grade)
        if count:
            query = query.limit(count)

        results = query.all()

        if shuffle:
            results = random.sample(results, len(results))
        
        return results

    @staticmethod
    def get_one(min_grade=0, max_grade=11) -> 'Lesson':
        res = Lessons.get_all(min_grade=min_grade, max_grade=max_grade, count=1)[0]
        assert isinstance(res, Lesson)
        return res

    @staticmethod
    def get_by_id(lesson_id) -> 'Lesson':
        query: Query = session.query(Lesson).filter_by(lesson_id=lesson_id+1)
        assert query.count() == 1
        res = query.one()
        assert isinstance(res, Lesson)
        return res


def initialize():
    """
    Adds lessons to database from json.
    """
    Base.metadata.create_all(engine)

    with open(Files.TextDataJson, 'r') as f:
        lesson_dicts: list = json.load(f)
    # TODO: reverse lessons in json instead of dynamically
    lesson_dicts.reverse()

    for lesson_dict in lesson_dicts:
        lesson: Lesson = Lesson(
            name=lesson_dict['name'], grade=lesson_dict['grade'], text=lesson_dict['text'])

        cloze_dict = lesson_dict.get('cloze', None)
        if cloze_dict:
            cloze: Cloze = Cloze(
                text=cloze_dict['text'], answers=repr(cloze_dict['answers']))
            lesson.cloze = cloze

        vocab = lesson_dict.get('vocab', None)
        if vocab:
            lesson.vocab = repr(vocab)

        session.add(lesson)

    session.commit()


if __name__ == "__main__":
    # initialize()
    # one = Lesson.get_by_id(1121+1)
    # print(one)
    all = Lessons.get_all(min_grade=10)
    print(all)