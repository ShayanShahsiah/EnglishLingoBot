import requests
import re
import os.path as OS
import subprocess
from uuid import uuid4
from fileHandler import FileFunctions, Files
from random import randrange


# split long text into multiple shorter paragraphs with maximum length len
def split_story(text: str, maxLen: int, result=list()):
    lenT = len(text)
    # look for newline
    for i in range(1, lenT):
        if text[i] == "\n" :
            result.append(text[0:i])
            split_story(text[i:lenT], maxLen, result)
            return
    if lenT < maxLen:
        result.append(text)
    else:
         
        # look for first period
        resultI = None
        for i in range(maxLen):
            if text[i] == "." and text[i+1] == ' ':
                resultI = i
        if resultI:
            result.append(text[0:resultI+1])
            split_story(text[resultI+1:lenT], maxLen, result)
            return
        # no period found, split by space instead
        for i in reversed(range(maxLen)):
            if text[i] == " ":
                result.append(text[0:i])
                split_story(text[i:lenT], maxLen, result)
                return

                
def smmlGen(text, speed = 100, gender: int = 0, variant: int = 1):
    """
    speed is percentage (100% is normal)
    gender is int, 0 not to use, 1 for male and 2 for female
    variant is voice variant
    """
    if gender is 1:
        gstring = "male"
    elif gender is 2:
        gstring = "female"
    else:
        gstring = None
    final = "<speak>"
    final += f'<prosody rate="{speed}%">'
    if gstring:
        final += f'<voice gender="{gstring}" variant="{variant}">'
    else:
        final += f'<voice variant="{variant}">'
    if text[0] == ' ':
        final += '<break strength="x-weak"/>'
        final += text[1:]
    elif text[0] == '\n':
        final += '<break strength="strong"/>'
        final += text[1:]
    else:
        final += text
    final += "</voice>"
    final += "</prosody>"
    final += "</speak>"
    return final


def appendMP3(sound1: bytes, sound2: bytes):
    """
    Append mp3 formatted bytes together
    """
    if sound1 is None:
        if sound2 is None:
            return None
        return sound2
    sound1 += sound2[20:]
    return sound1


def synthesis(text: str, option=0, speed = 100, userAgent="Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0"):
    """
    Usage:
        synthesis(text to get, language option, user agent)
        options:
            0 -> Random American male/female
            1 -> United States male voice
            2 -> United States female voice
            3 -> British male voice
            4 -> British female voice
            5 -> Austrailian male voice
            6 -> Austrailian female voice
        speed:
            percentage of speed to read at(100 is default)
        output:
            returns:
                resultant bytes in mp3 format
    """
    if option is 1 or option is 0:
        voice = "en-US-Wavenet-A"
    elif option is 2:
        voice = "en-US-Wavenet-C"
    elif option is 3:
        voice = "en-GB-Wavenet-D"
    elif option is 4:
        voice = "en-GB-Wavenet-C"
    elif option is 5:
        voice = "en-AU-Wavenet-B"
    elif option is 6:
        voice = "en-AU-Wavenet-A"
    else:
        print("Option not implemented")
        return None
    texts = []

    split_story(text, 850, texts)
    with requests.Session() as session:
        session.headers = {
            "Host": "spik.ai",
            "User-Agent": userAgent,
        }
        page = session.get("https://spik.ai/").text
        token = re.search(r"csrfmi.*?value='(.*?)'", page).group(1)
        session.headers.update ({
            "Origin": "https://spik.ai",
            "Referer": "https://spik.ai/",
        })
        audioLinkRe = re.compile(r'a href="(\/generate.*?)"')
        result = None
        variant = randrange(1,5)
        gender = 0
        if not option:
            gender = randrange(1,3)
        for subtext in texts:
            smmldata = smmlGen(subtext, speed, gender, variant)
            data = {
                "csrfmiddlewaretoken": token,
                "text_to_generate": smmldata,
                "voice_type": voice,
                "text_or_ssml": "ssml",
                "button": ""
            }
            page = session.post("https://spik.ai/generate/", data=data).text
            audioLink = re.search(audioLinkRe, page).group(1)
            audio = session.get("https://spik.ai" + audioLink, headers="")
            result = appendMP3(result, audio.content)
        return result

if __name__ == "__main__":
    text = "A Baby\nA baby has arms and legs. It has a mouth and eyes. It looks at everything.\nIt eats everything. It smiles a lot. It cries a lot. It eats a lot. It drools a lot. It pees a lot.\nIt poops a lot. It sleeps a lot. It tries to talk. It makes funny sounds. It says \"Googoo\" and \"Gaga.\" It waves its arms and legs. It doesn't do much else. It doesn't sit up. It doesn't stand up. It doesn't talk. It lies on its back. It lies on its stomach. After a year, it will do many things. It will crawl. It will stand up. It will walk. It will talk. But in the beginning, it just grows. It grows bigger and bigger."
    # for i in texts:
    #     print(smmlGen(i))
    # smmlGen(text)
    with open("res.mp3", 'wb') as f: 
        f.write(synthesis(text, 2))
