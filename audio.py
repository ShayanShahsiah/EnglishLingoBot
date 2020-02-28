import requests
import re
import os.path as OS
from uuid import uuid4
__Audio_Folder = OS.join(OS.dirname(OS.abspath(__file__)), "Audio")
def recognition():
    pass
#split long text into multiple shorter paragraphs with maximum length len
def splitStory(text: str, maxLen: int, result = list()):
    if len(text) < maxLen:
        result.append(text)
    else:
        #look for first period
        lenT = len(text)
        resultI = None
        for i in range(maxLen):
            if text[i] == "." and text[i+1] == " ":
                resultI = i
        if resultI:
            result.append(text[0:resultI+1])
            splitStory(text[resultI+2:lenT], maxLen, result)
            return
        #no period found, split by space instead
        for i in reversed(range(maxLen)):
            if text[i] == " ":
                result.append(text[0:i+1])
                splitStory(text[i+1:lenT], maxLen, result)
                return

def synthesis(text: str, option = 1, userAgent="Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0"):
    """
    Usage:
        synthesis(text to get, language option, user agen)
        options:
            1 -> United States male voice
            2 -> United States female voice
            3 -> British male voice
            4 -> British female voice
            5 -> Austrailian male voice
            6 -> Austrailian female voice
        output:
            returns:
                base file name that it's saved as
            saved audio in parts into the audio folder specified in the file with maximum 300 chars each
            base file name is randomly generated for each text
    """
    if option is 1:
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

    # 300-char limit not applied right now for some reason
    #if len(text) > 300:
    if False:
        splitStory(text, 300, texts)
    else:
        texts.append(text)
    fileName = str(uuid4())
    with requests.Session() as sess:
        sess.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Host": "spik.ai",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": userAgent,
        }
        page = sess.get("https://spik.ai/").text
        token = re.search(r"csrfmi.*?value='(.*?)'", page).group(1)
        sess.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Content-Length": "156",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": f"csrftoken={token}",
            "Host": "spik.ai",
            "Origin": "https://spik.ai",
            "Referer": "https://spik.ai/",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0",
        }
        audioLinkRe = re.compile(r'a href="(\/generate.*?)"')
        nameCounter = 1
        for subtext in texts:
            data = {
                "csrfmiddlewaretoken": token,
                "text_to_generate": subtext,
                "voice_type": voice,
                "text_or_ssml": "text",
                "button": ""
            }
            page = sess.post("https://spik.ai/generate/", data=data).text
            with open("test.html", 'w') as f:
                f.write(page)
            audioLink = re.search(audioLinkRe, page).group(1)
            with open(OS.join("Audio", f"{fileName}.{nameCounter}.mp3"), 'wb') as f:
                audio = sess.get("https://spik.ai" + audioLink, headers = "")
                f.write(audio.content)
            nameCounter += 1
        return fileName

if __name__ == "__main__":
    text = "A baby has arms and legs. It has a mouth and eyes. It looks at everything. It eats everything. It smiles a lot. It cries a lot. It eats a lot. It drools a lot. It pees a lot. It poops a lot. It sleeps a lot. It tries to talk. It makes funny sounds. It says \"Googoo\" and \"Gaga.\" It waves its arms and legs. It doesn't do much else. It doesn't sit up. It doesn't stand up. It doesn't talk. It lies on its back. It lies on its stomach. After a year, it will do many things. It will crawl. It will stand up. It will walk. It will talk. But in the beginning, it just grows. It grows bigger and bigger. 0.0\n"
    synthesis(text, 1)