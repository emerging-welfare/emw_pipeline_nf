import argparse
import re
import lxml.html
from fuzzywuzzy import fuzz
# from utils import dump_to_json
from utils import load_from_json
from utils import write_to_json
from utils import change_extension

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', help="Path to input file")
    parser.add_argument('--out_dir', help="Path to output folder")
    parser.add_argument('--data', help="Serialized json string")
    parser.add_argument('--source', help="Source of the article")
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

def deletecertainstr(lines, stoplist1=None, stoplist2=None, stoplist3=None):

    if stoplist1 is not None:
        for i in range(0,len(lines)):
            firstline = lines[i]
            # firstline = firstline.strip()
            firstline = re.sub(r"\n|\r", r"", firstline)
            if any(firstline == word for word in stoplist):
                for j in range(i, len(lines)):
                    del lines[i]
                break

    if stoplist2 is not None:
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

    if stoplist3 is not None:
        firsttime = True
        for i in range(0,len(lines)):
            firstline = lines[i]
            firstline = firstline.strip()
            if firsttime:
                if re.search(r"\d{2}:\d{2} IST", firstline):
                    firsttime = False
                continue
            else:
                j = i
                n = len(lines)
                while j < n:
                    line = lines[j].strip()
                    time = re.search(r"\d{2}:\d{2}IST", line)
                    if time or any(line == word for word in stoplist):
                        del lines[j]
                        n = n - 1
                        continue
                    j = j + 1
                break

    return [line for line in lines if line != ""]

# Ugly as hell
def addnewstime(lines, html_string, data, source, stoplist=None):

    doc = lxml.html.document_fromstring(html_string)
    if source == 1:

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

            data["title"] = title
            data["time"] = time

    elif source == 2:
        title = doc.xpath("//h1[@class='ArticleHead']/text()")
        time = doc.xpath("//p[@class='ArticlePublish' and position()=1]/span/text()")
        if not time:
            time = doc.xpath("//input[@class='article_created_on']/@value")

        if not title:
            title = doc.xpath("//meta[@name='title']/@content")

            if not title:
                title = doc.xpath("//title/text()")

        if title and time:
            title = str(title[0]).strip()
            time = str(time[-1]).strip()
            lines.insert(0,time)
            lines.insert(0,title)
            data["title"] = title
            data["time"] = time

    elif source == 3:
        title = doc.xpath("//title/text()")
        time = doc.xpath("//div[@class='story-date']/text()")
        if time is None:
            time = doc.xpath("//div[@class='posted'/strong[last()]/text()")

        if time:
            time = "".join([i for i in time])
            lines.insert(0,time)
            data["time"] = time

        title = "".join([i for i in title])
        lines.insert(0,title)
        data["title"] = title

    elif source == 4:
        place = re.search(r'var datelineStr\s*=\s*"([^"]*)"', str(html_string))
        if place:
            place = place.group(1)

        title = doc.xpath("//h1[@class='artcl-nm-stky-text']/text()")
        if not place:
            place = doc.xpath("//meta[contains(@property,'section')]/@content")
            place = str(place[0])

        if not title:
            title = doc.xpath("//title/text()")

        if title:
            title = str(title[0]).strip()
            data["title"] = title
            if not any(fuzz.ratio(title,line)>70 for line in lines):
                lines.insert(0,title)

        if place:
            place = place.strip()
            if place not in stoplist:
                lines.insert(0,place)
                data["place"] = place

    elif source == 5:
        has_time = False
        for i,line in enumerate(lines):
            line = line.strip()
            if ("UPDATED : " in line):
                has_time = True
                del lines[i]
                break

        title = doc.xpath("//title/text()")
        time = doc.xpath('//div[@itemprop="dateCreated"]/text()')
        if title:
            title = title[0].strip()
            data["title"] = title
            if not any(re.sub(r"[ \n\r\t]", r"", title) == re.sub(r"[ \n\r\t]", r"", line) for line in lines):
                if not has_time:
                    lines.insert(0,title)

        if time:
            time = time[0].strip()
            data["time"] = time
            if not has_time:
                lines.insert(0,time)

    elif source == 6:
        title = doc.xpath("//div[@id='p_title']/text()")
        if not title:
            title = doc.xpath("//span[@id='p_title']/text()")
        if not title:
            title = doc.xpath("//div[@id='ivs_title']/text()")

        time = doc.xpath("//div[@id='ivs_publishtime']/text()")
        if not time:
            time = doc.xpath("//div[@id='p_publishtime']/text()")
        if not time:
            time = doc.xpath("//span[@id='p_publishtime']/text()")

        if time:
            time = "".join([i for i in time])
            data["time"] = time
            if lines.count(time) == 0:
                lines.insert(1 if len(lines) > 1 else 0, time)

        if title:
            title = "".join([i for i in title])
            data["title"] = title
            if lines.count(title) == 0:
                lines.insert(0,title)

    return lines, data


def main(args):

    # Source 1 times
    # Source 2 newind
    # Source 3 ind
    # Source 4 thehin
    # Source 5 scm
    # Source 6 people

    data = load_from_json(args.data)
    filename = args.input_dir + "/" + data["id"]

    with open(filename, "rb") as g:
        html_string = g.read()

    text = data["text"].splitlines()

    stoplist1 = None
    stoplist2 = None
    stoplist3 = None
    stoplist4 = None
    if args.source == 1:
        text = deletesamesubstr(text)
        stoplist1 = ["RELATED", "From around the web", "More from The Times of India", "Recommended By Colombia",
                     "more from times of india Cities","You might also", "You might also like", "more from times of india",
                     "All Comments ()+^ Back to Top","more from times of india News","more from times of india TV",
                     "more from times of india Sports","more from times of india Entertainment","more from times of india Life & Style",
                     "more from times of india Business"]
        stoplist2 = ["FOLLOW US","FOLLOW PHOTOS","FOLLOW LIFE & STYLE"]

    elif args.source == 3:
        stoplist1 = ["Tags:","ALSO READ","Please read our before posting comments","TERMS OF USE: The views expressed in comments published on indianexpress.com are those of the comment writer's alone. They do not represent the views or opinions of The Indian Express Group or its staff. Comments are automatically posted live; however, indianexpress.com reserves the right to take it down at any time. We also reserve the right not to publish comments that are abusive, obscene, inflammatory, derogatory or defamatory."]

    elif args.source == 4:
        stoplist3 = ["ShareArticle","Updated:","MoreIn","SpecialCorrespondent","METRO PLUS","EDUCATION PLUS","PROPERTY PLUS","CINEMA PLUS","DISTRICT PLUS"]
        stoplist4 = ["METRO PLUS","EDUCATION PLUS","PROPERTY PLUS","CINEMA PLUS","DISTRICT PLUS"]

    elif args.source == 5:
        stoplist1 = ["Print Email","Video"]
        stoplist2 = ["Viewed","Associated Press","Get updates direct to your inbox","Opinion"]


    elif args.source == 6:
        stoplist2 = ['Email | Print', '+', 'stumbleupon', 'More Pictures', 'Save Article', 'Click the "PLAY" button and listen. Do you like the online audio service here?','Good, I like it','Do you have anything to say?','Name']
        text = [line for line in text if not line.startswith("Source")]

    if text:
        text = deletecertainstr(text, stoplist1=stoplist1, stoplist2=stoplist2, stoplist3=stoplist3)
        if text:
            text, data = addnewstime(text, html_string, data, args.source, stoplist=stoplist4)
            if args.source == 1:
                text = deletesamesubstr(text)
            if text:
                text = "".join([line.strip() + "\n" if line.strip() != "" else "" for line in text])[:-1]
                data["text"] = text

    return data

if __name__ == "__main__":
    args = get_args()
    data = main(args)
    # print(dump_to_json(data))
    write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
    print('"' + change_extension(data["id"], ex=".json") + '"')
