import re
import lxml.html
from fuzzywuzzy import fuzz
from utils import remove_path # !!!
from utils import read_from_json # !!!
from utils import write_to_json # !!!

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help="Path to input file")
    args = parser.parse_args()
    return args

def deletesamesubstr(lines):
    i = 0
    while i <= len(lines)-1:
        isDeleted = False
        firstline = lines[i]
        firstline = re.sub(r"\W", r"", firstline)
        firstline = re.sub(r"<[^>]*>", r"", firstline)
        for j in range(i+1,len(lines)):
            secondline = lines[j]
            secondline = re.sub(r"\W", r"", secondline)
            if firstline.lower() in secondline.lower() and len(firstline)>22:
                del lines[i]
                isDeleted = True
                break

        if not isDeleted:
            i = i + 1

    return [line for line in lines if line != ""]

def deletecertainstr(lines, stoplist, stoplist2):

    for i in range(0,len(lines)):
        firstline = lines[i]
        firstline = firstline.strip()
        if any(firstline == word for word in stoplist):
            for j in range(i, len(lines)):
                del lines[i]
            break

    n = 0
    while n < len(lines)-1:
        if not lines[n]:
            n = n + 1
            continue
        line = lines[n].strip()
        if any(line == word for word in stoplist2):
            del lines[n]
            continue
        n = n + 1

    return [line for line in lines if line != ""]

def addnewstime(lines, html_string):

    doc = lxml.html.document_fromstring(html_string)
    title = doc.xpath("//h1[@class='heading1']/text()")
    time = doc.xpath("string(//span[@class='time_cptn'])")

    if not title:
        title = doc.xpath("//title/text()")

    if title and time:
        title = str(title[0]).strip()
        time = str(time).strip()
        if not any(fuzz.ratio(title,line)>70 for line in lines):
            lines.insert(0,time)
            lines.insert(0,title)

    return lines, title, time


def main(args):
    stoplist = ["RELATED", "From around the web", "More from The Times of India", "Recommended By Colombia",
            "more from times of india Cities","You might also", "You might also like", "more from times of india",
            "All Comments ()+^ Back to Top","more from times of india News","more from times of india TV",
            "more from times of india Sports","more from times of india Entertainment","more from times of india Life & Style",
            "more from times of india Business"]
    stoplist2 = ["FOLLOW US","FOLLOW PHOTOS","FOLLOW LIFE & STYLE"]

    filename = args.input_file
    with open(filename, "rb") as g:
        html_string = g.read()

    filename = remove_path(filename)
    data = read_from_json(args.out_dir + filename)
    text = data["text"].splitlines()

    text = deletesamesubstr(text)
    if text:
        text = deletecertainstr(text, stoplist, stoplist2)
        if text:
            text, title, time = addnewstime(text, html_string)
            if title and time:
                data["title"] = title
                data["time"] = time

            text = deletesamesubstr(text)
            if text:
                text = "".join([line.strip() + "\n" if line.strip() != "" else "" for line in text])[:-1]
                data["text"] = text
                write_to_json(data, args.out_dirs + filename + ".json")

if __name__ == "__main__":
    args = get_args()
    main(args)
