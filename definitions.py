import csv
from typing import Dict, List

class Definitions:
    def __init__(self):
        self._dict: Dict[str, List[str]] = dict()

        with open('en_to_fa_dict.csv', 'r') as csv_file:
            content = csv.reader(csv_file, delimiter=',')
            for row in content:
                if self._dict.get(row[0], None):
                    self._dict[row[0]].append(row[1])
                else:
                    self._dict[row[0]] = [row[1]]

    def translate(self, word: str) -> List[str]:
        res = self._dict.get(word, None)
        if res:
            return res
        else:
            return []

if __name__ == '__main__':
    defs = Definitions()
    print(defs.translate('tree'))