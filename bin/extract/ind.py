from lxml import etree
import re
import argparse

import sys
sys.path.append("..")
from utils import remove_path
from utils import write_to_json
from utils import change_extension

def stringify_children(node):
    s = node.text
    if s is None:
        s = ''
    if node.tail:
        s = s + node.tail
    for child in node:
        if child.tag != "div":
            s += '\n' + re.sub(r" {2,}|\n|\r|\t", r"", stringify_children(child))
    return s

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', help="Path to input file")
    parser.add_argument('--out_dir', help="Path to output folder")
    args = parser.parse_args()
    return args

def main(args):
    filename = args.input_file
    with open(filename, "rb") as f:
        html_string = f.read()

    stoplist = ["... contd.", "Please read our terms of use before posting comments"]

    filename = remove_path(filename)
    data = {}
    data["id"] = filename

    htmlparser = etree.HTMLParser(remove_comments=True)
    doc = etree.HTML(html_string, htmlparser)
    node = doc.xpath('//div[contains(@class, "contentstory")]')
    if node:
        text = ""
        for s in [re.sub(r" {2,}|\n|\t|\r", r"", x) for x in doc.xpath('//div[contains(@class, "contentstory")]/text()')]:
            if s:
                text += s
                break
        text += stringify_children(node[0])
    else:
        node = doc.xpath('//div[@class="txt"]')
        if node:
            text = stringify_children(node[0])
        else:
            text = "".join(doc.itertext(tag="p"))
            if not text:
                text = ""

    # Clean
    lines = text.splitlines()
    for i in range(0,len(lines)):
        firstline = lines[i]
        firstline = re.sub(r"\n|\r", r"", firstline)
        if any(firstline == word for word in stoplist):
            for j in range(i, len(lines)):
                del lines[i]
            break
    text = "\n".join([line for line in lines if re.search("\S", line)])

    # Add time and title
    title = doc.xpath("//title/text()")
    time = doc.xpath("//div[@class='story-date']/text()")
    if time is None:
        time = doc.xpath("//div[@class='posted'/strong[last()]/text()")
    if time:
        time = "".join([i for i in time])
        lines.insert(0,time)
        data["time"] = time
    title = "".join([i for i in title])
    if title:
        lines.insert(0,title)
        data["title"] = title

    data["text"] = text
    # data = dump_to_json(data)
    return data

if __name__ == "__main__":
    args = get_args()
    data = main(args)
    # print(data)
    write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
    print('"' + change_extension(data["id"], ex=".json") + '"')
