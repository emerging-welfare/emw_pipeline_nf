# !/usr/bin/env python3
#This Script was written by Cagil Orignally, adjusts are made by aalabrash18@ku.edu.tr
# - *- coding: utf- 8 - *-

import argparse, os, sys, io, traceback, codecs
from bs4 import BeautifulSoup, Comment
UNESCAPE = True
import html as h
from lxml import etree
import re
from utils import remove_path
from utils import dump_to_json

# Ignore converting links from HTML


def check_encoding(input_dir):
    pos_count = 0
    count = 0
    for dirname, _, filenames in os.walk(input_dir):
        for filename in filenames:
            full_name = os.path.join(dirname, filename)
            content = []
            if full_name.endswith(".DS_Store") or full_name.endswith(".meta"):
                continue
            elif os.path.getsize(full_name) > 0:
                pos_count += check_encoding_file(full_name)
            else:
                print("%s is empty" % (full_name))
        count += 1
    print("Checked %s files, %s is ok" % (count, pos_count))


def check_encoding_file(full_name):
    with codecs.open(full_name, "r", "utf-8") as inputfile:
        # with io.open(full_name,"r") as inputfile:
        try:
            content = inputfile.read()
            if check_encoding_string(h.unescape(content)):
                UNESCAPE = True
            elif check_encoding_string(h.unescape(content.encode("latin1"))):
                LATIN = True
                print("%s is Latin encoded" % (full_name))
            else:
                print("%s is not Portuguese" % (full_name))
                return False
        except UnicodeDecodeError:
            pass  # print("Couldn't read %s" %full_name)
    return True


def check_encoding_string(content):
    try:
        count = max(content.count(u"í"), content.count(u"á"), content.count(u"é"), content.count(u"ã"))
    except UnicodeDecodeError:
        try:
            content_utf = content.decode("utf8")
            count = max(content_utf.count(u"í"), content_utf.count(u"á"), content_utf.count(u"é"),
                        content_utf.count(u"ã"))
        except:
            traceback.print_exc()
            sys.stderr.write("Problem in check_encoding_string")
            count = 0
    if count < 1:
        return False
    return True


def write_parsed_page_alt(infilename):
    content, title, time,w = parse_page_alternative(infilename)
    if content is None or content is u"":
        sys.stderr.write("Empty result return for %s.\n" % infilename)
        return (' ', None)
    if check_encoding_string(content):
        pass
    elif check_encoding_string(content):
        content = content.encode()
        title = title.encode()
    return (content, title, time,w)
    if debug:
        print("[CLEANED CONTENT] %s\n" % content)
        # sys.stdout.write("[UNICODE CONTENT] %s\n" %unicode_content)
        # sys.stdout.write("[INFILENAME]%s\n" %infilename)
        sys.stdout.write("[OUTFILENAME]%s\n" % infilename)
        sys.stdout.write("************************************************************\n")
        sys.stdout.write("************************************************************\n")


def parse_page_alternative(infilename):
    page = get_soup_page(infilename)
    htmlparser = etree.HTMLParser(remove_comments=True)
    doc = etree.HTML(open(infilename, "r",encoding="latin1").read(), htmlparser)
    title = get_title(doc, page)
    time = get_time(page)
    clean_page(page)
    clean_more(page)
    warning=False
    tags=set([tag.name for tag in page.find_all()])
    # value = unicode(page.find("body"))
    try:
        value=""
        #value = page.find("body").getText()
        #value=page.find("arttextxml").getText().strip().lstrip() if "arttextxml" in tags else  page.find('div', attrs={'class': 'article_content clearfix'}).getText().strip().lstrip()
        if "arttextxml" in tags:
            value = page.find("arttextxml").getText().strip().lstrip()
        if len(value)<3 :
            value=page.find('div', attrs={'class': 'article_content clearfix'}).getText().strip().lstrip()
        mylist = [re.sub(r"^\s+|\s+$", "", x) for x in value.split("\n") if not re.match(r"^ {1,}$",x)]
        mylist=[x for x in mylist if x!=""]
        if mylist:
            return "\n".join(mylist), title, time,warning
    except :
        pass
    try:
        value = page.find("body").getText()
        warning=True
    except AttributeError:
        traceback.print_exc()
        sys.stderr.write("No body in %s\n" % infilename)
        return None, None
    content_raw = ''.join(BeautifulSoup(value, "html.parser").findAll(text=True))
    mylist = content_raw.split("\n")
    mylist_cleaned = []
    mylist=[x.strip().lstrip() for x in mylist if len(x) > 2]
    for i,item in enumerate(mylist):
        re_item=re.match(r"^[A-Za-z][A-Za-z0-9]",item)
        if re_item  and i<len(mylist)-2:
            mylist_cleaned.append(item.strip().lstrip())
    content = "\n".join([line for line in mylist_cleaned if line.strip() is not u"" and len(line.split(" ")) > 3])
    if content is u"":
        value = page.text
        content_raw = ''.join(BeautifulSoup(value, "html.parser").findAll(text=True))
        mylist = content_raw.split("\n")
        mylist_cleaned = []
        for item in mylist:
            if len(item.strip().lstrip()) > 2:
                mylist_cleaned.append(item.strip().lstrip())
        content = "\n".join([line for line in mylist_cleaned if line.strip() is not u"" and len(line.split(" ")) > 3])
    if warning:
        print("This link might be not relative\t",infilename.split("/")[-1].replace("___", "://").replace("_", "/"))

    return content, title, time,warning


def get_soup_page(infilename):
    try:
        with io.open(infilename, 'r') as infile:
            page = BeautifulSoup(infile, "html.parser")
    except:
        with io.open(infilename, 'r', encoding="latin1") as infile:
            page = BeautifulSoup(infile, "html.parser")
    return page


def get_title(doc, page):  # can get rid of infilename and exceptions
    title = doc.xpath("//title/text()")
    title = "".join([i for i in title])
    if title:
        return title
    else:
        try:
            title = page.find("title").getText().strip(u"Folha de S.Paulo").strip("-").strip()
        except AttributeError:
            traceback.print_exc()
            sys.stderr.write("Title AttributeError at %s\n" % infilename)
            title = u" "
        except TypeError:
            sys.stderr.write("Title TypeError at %s\n" % infilename)
            title = u" "
            return title


def get_time(page):
    spans = page.find_all('span', {'class' : 'time_cptn'})
    if spans:
        lines = [span.get_text() for span in spans]
        return " ".join(" ".join(lines).split("|")[-1].rstrip().lstrip().split(":")[1:])
    
    divs=page.find('div', attrs={'class' : 'authorview clearfix'})
    if divs:
        divs=divs.findAll("span",attrs={"class":"av_i"})
        lines = [div.get_text() for div in divs]
        return " ".join(" ".join(lines).lstrip().split(":")[1:]).lstrip()
    divs=page.find("div",{"class","clearfix publish_info"})
    if divs:
        lines = [div.get_text() for div in divs]
        return " ".join(" ".join(lines).lstrip().split(":")[1:]).lstrip()
    return None


def clean_page(page):
    scripts = page.findAll("script")
    [scr.extract() for scr in scripts]
    styles = page.findAll("style")
    [scr.extract() for scr in styles]
    iframes = page.findAll("iframe")
    [scr.extract() for scr in iframes]
    comments = page.findAll(text=lambda text: isinstance(text, Comment))
    [comment.extract() for comment in comments]


def clean_more(page):
    imgs = page.findAll("img")
    [img.extract() for img in imgs]
    # brs = page.findAll("br")
    # [br.extract() for br in brs]
    links = page.findAll("a")
    [link.extract() for link in links]




def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', help="Path to input file") 
    parser.add_argument('--no_byte', help="If html file needs to be read with 'r' tag.", action="store_true") # Only pass for scmp articles
    args = parser.parse_args()
    return args

def main(args):
    filename = args.input_file    
    content,title,time=write_parsed_page_alt(filename) 
    filename = remove_path(filename)
    data={}
    data["id"] = filename
    data["title"]=title
    data["text"] = title+"\n"+time+"\n"+content
    data = dump_to_json(data) 
    return data   

if __name__ == "__main__":
    args = get_args()    
    data = main(args)    
    print(data)
