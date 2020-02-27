import requests
import os
import json
import re
from html import unescape
from bs4 import BeautifulSoup
import json
#something

_working_dir = os.path.dirname(os.path.abspath(__file__))
_database_dir_abs = os.path.join(_working_dir, "Data")
if not os.path.exists(_database_dir_abs):
    os.mkdir(_database_dir_abs)
#deprecated:
#wrapper to save funciton outputs to corresponding file //NOTE that only works correctly when function returns list of objects
def saveToFile(function):
    def saver(*args, **kwargs):
        data = function(*args, **kwargs)
        fileName = os.path.join(_database_dir_abs, f"{function.__name__}.json")
        if not os.path.exists(fileName):
            with open(fileName, 'w') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        else:
            fileContent = None
            with open(fileName, 'r') as f:
                fileContent = json.load(f)
            for element in data:
                if element not in fileContent:
                    fileContent.append(element)
            with open(fileName, 'w') as f:
                json.dump(fileContent, f, indent=4)
        print("Saved for " + function.__name__)
    return saver
#simple method to return text without adding so many parameters
def getText(url, headers=""):
    return requests.get(url, headers=headers).content.decode("utf-8", 'ignore')
def removeTags(string: str):
    return re.sub(r'<[^>]+>', '', string)
class Extractor():
    ClozeTestEmptyWordSpecifier = "<+===+>"
    fileNameGrabberRe = re.compile(r'name": "(.*?)(?<!\\)"')
    gradeGrabberRe = re.compile(r'"grade": ("[0-9]*\.[0-9]*?")')
    #save to file periodically, prevents high memory usage. takes in an object as input and saves in a list
    def saveToFile(self, data, fileName, ensureNoRepetitions=False):
        fileName = os.path.join(_database_dir_abs, f"{fileName}.json")
        if not os.path.exists(fileName):
            with open(fileName, 'w') as f:
                f.write('[\n')
                f.write(json.dumps(data, ensure_ascii=False))
                f.write('\n]')
        else:
            if not ensureNoRepetitions:
                with open(fileName, 'r') as f:
                    for line in f:
                        find = re.search(self.fileNameGrabberRe, line)
                        if find:
                            if data["name"] == find.group(1):
                                return False
            #remove last character
            with open(fileName, 'rb+') as filehandle:
                filehandle.seek(-1, os.SEEK_END)
                filehandle.truncate()
            with open(fileName, 'a') as f:
                f.write(',\n')
                f.write(json.dumps(data, ensure_ascii=False))
                f.write('\n]')
        return True
    def checkRepetitions(self, storyname, fileName):
        path = os.path.join(_database_dir_abs, f"{fileName}.json")
        try:
            with open(path, 'r') as f:
                for line in f:
                    find = re.search(self.fileNameGrabberRe, line)
                    if find:
                        if storyname == find.group(1):
                            return True
        except FileNotFoundError:
            return False
        return False
    #this doesn't override the data
    def fixErrors(self, fileName, readableFormat=True):
        print("start")
        # Fix names and change grade type to int:
        path = os.path.join(_database_dir_abs, f"{fileName}.json")
        temp = os.path.join(_database_dir_abs, f"{fileName}.clean.json")
        with open(path, 'r') as original:
            with open(temp, 'w') as tempFile:
                for line in original:
                    findName = re.search(self.fileNameGrabberRe, line)
                    findGrade = re.search(self.gradeGrabberRe, line)
                    replacedText = line
                    if findName:
                        replacedText = replacedText.replace(findName.group(1), findName.group(1).replace(r'\n', '').replace('*', ''))
                    if findGrade:
                        replacedText = replacedText.replace(findGrade.group(1), findGrade.group(1).replace(r'"', ''))
                    tempFile.write(replacedText)
        #Fix order; sort by grade order, remove duplicates and save to readable format optionally
        #Note that this loads to RAM, might not work with bigger file sizes
        data = None
        with open(temp, 'r') as f:
            data = json.load(f)
        #sort
        data = sorted(data, key=lambda k: k['grade'], reverse=True)
        #remove duplicates
        new_d = []
        for x in data:
            if x not in new_d:
                new_d.append(x)
        data = new_d
        #save
        with open(temp, 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"done for {len(data)} unique stories")
    def eslyes(self, links: list):
        """
        extract from https://eslyes.com/supereasy/
        parameter: list of links to get data from, also extracts "quiz" data
        returns: data object of result in jsonable format
        Currently supported quiz types: Vocabulary and Cloze
        """
        FILENAME = "eslyes"
        #list of stories extracted
        baseURLre = re.compile(r'(.*\/)')
        extractorMainLinksRe = re.compile(r'a href="(.*?)">\w*\.\s(.*?)<.*?(\w\.\w)')
        extractorStoryRe = re.compile(r'msonormal.*?>(?:\s*[0-9]+\.\s*)?(.*?)\s*<', re.DOTALL)
        cleanupRe = re.compile(r'(.*\.)(?:\s*[0-9]+\.[0-9]+)')
        ####
        vocabExtractorRe = re.compile(r'dictionary.*?>(.*?)<')
        ####
        clozeBlockRe = re.compile(r'(<div class="ClozeBody".*?div>)', re.DOTALL)
        dataFromBlocksRe = re.compile(r'>\s*?([^\n]*?)\s*?<')
        answersRe = re.compile(r"\s=\s\'(\\.*?)\'")

        for link in links:
            print(f"ENTERING LINK {link}\n")
            baseURL = re.search(baseURLre, link).group(1)
            webpage = getText(link)
            if link == "https://eslyes.com/eslread/":
                extractorMainLinksRe = re.compile(r'\w*\. <a href="(.*?)">(.*?)<.*?([0-9]+\.[0-9]+)', re.DOTALL)
            try:
                for subURL, name, grade in re.findall(extractorMainLinksRe, webpage):
                    subStory = dict()
                    Name = unescape(name).strip()
                    if (self.checkRepetitions(Name, FILENAME)):
                        print("repeated")
                        continue
                    print(f"entering for story {Name}")
                    subStory["name"] = Name
                    subStory["grade"] = grade
                    subStory["text"] = ""
                    if "http" in subURL:
                        fullURL = subURL
                    else:
                        fullURL = baseURL + subURL
                    webpage = getText(fullURL)
                    #Extract cleaned up Story paragraph:
                    storyParts = re.findall(extractorStoryRe, webpage) 
                    with open("test.html", 'w') as f:
                        f.write(webpage)
                    for i in range(len(storyParts)):
                        subtext = unescape(storyParts[i])
                        if i+1 == len(storyParts):
                            cleaned = re.search(cleanupRe, subtext)
                            if cleaned:
                                subStory["text"] += cleaned.group(1)
                            else:
                                subStory["text"] += subtext
                            break
                        subStory["text"] += subtext + '\n'
                    #Extract quizzez
                    soup = BeautifulSoup(webpage, 'html.parser')
                    for element in soup.find_all("a", attrs={"target": "_blank"}):
                        if "Vocab" in element.text:
                            print("Getting vocab")
                            url = baseURL + element["href"].replace(r'../', '', 1)
                            vocabPage = getText(url)
                            subStory["vocab"] = list()
                            for word in re.findall(vocabExtractorRe, vocabPage):
                                subStory["vocab"].append(word)
                        elif "Cloze" in element.text:
                            print("Getting cloze")
                            url = baseURL + element["href"].replace(r'../', '', 1)
                            clozePage = getText(url)
                            try:
                                block = re.search(clozeBlockRe, clozePage).group(1)
                            except:
                                continue
                            subStory["cloze"] = dict()
                            subStory["cloze"]["text"] = ""
                            for dataChunk in re.findall(dataFromBlocksRe, block):
                                if dataChunk:
                                    subStory["cloze"]["text"] += unescape(dataChunk) + " " + self.ClozeTestEmptyWordSpecifier
                            #remove trailing string
                            subStory["cloze"]["text"] = subStory["cloze"]["text"][:-(len(self.ClozeTestEmptyWordSpecifier))]
                            answersList = list()
                            for answer in re.findall(answersRe, clozePage):
                                answersList.append(answer.encode().decode('unicode-escape'))
                            subStory["cloze"]["answers"] = answersList
                    self.saveToFile(subStory, FILENAME, True)
            except KeyboardInterrupt:
                print("Exiting..")
                break
extractor = Extractor()
extractor.fixErrors("eslyes")
# extractor.eslyes(["https://eslyes.com/easykids/", "https://eslyes.com/nnse/", "https://eslyes.com/children/", "https://eslyes.com/extra/contents.htm", "https://eslyes.com/eslread/"])
# extractor.eslyes(["https://eslyes.com/supereasy/", "https://eslyes.com/easyread/", "https://eslyes.com/inter/contents.htm"])