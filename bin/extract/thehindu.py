#!/usr/bin/env python
from lxml import etree
import re
from utils import remove_path
#from utils import dump_to_json  
from utils import write_to_json
from utils import change_extension
import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', help="Path to input file")
    parser.add_argument('--out_dir', help="Path to output folder")
    args = parser.parse_args()
    return args

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

def get_time(doc):
    #take the publishing time only 
    time=doc.xpath('//div[contains(@class,"ut-container")]')
    if len(time)>0:
        time_txt_ls= [stringify_children(x).strip("\n") for x in time]
        if len(time_txt_ls)>2:
            return re.search(r"\S{1,} \d{2}, \d{4} \d{2}:\d{2}", time_txt_ls[1]).group()
        else:
            return re.search(r"\S{1,} \d{2}, \d{4} \d{2}:\d{2}", time_txt_ls[0]).group()#str(time_txt_ls[1]).strip("\n") if len(time_txt_ls)>2 else str(time_txt_ls[0]).strip("\n")

def main(filename):
        unvaild_pages=set(["photo-stories","recipes","bollywood","slideshow","relationships","bollywood-unknown_photo-stories","cartoon","Weather","Cartoonscape","cartoonscape"])
        if set.intersection(set(remove_path(filename).split("_")), unvaild_pages):
            return {"id":remove_path(filename),"text":"Not available","title":"Not Availabile","time":"Not Available"}
        with open(filename, "rb") as f:
            html_string = f.read()
        filename = remove_path(filename)
        data = {}
        data["id"] = filename
        htmlparser = etree.HTMLParser(remove_comments=True)
        doc = etree.HTML(html_string, htmlparser)
        #node = doc.xpath('//div[contains(@class, "article")]') 
        node =doc.xpath('//p')
        #node = doc.xpath('//div[contains(@class, "article")]')
        if not node:
            node =doc.xpath('//div/p')
        if not node:
            node=doc.xpath('//div[contains(@id,"content-body")]')
        if node:
            lines="".join([stringify_children(x) for x in node]).split("\n")
        else:
            return {"id":filename,"text":"Not available","title":"Not Availabile","time":"Not Available"}
        if "Share Via Email" in lines:
            lines.remove("Share Via Email")
        text = "\n".join([line for line in lines if re.search("\S", line)])
        
        # Add time and title
        data["title"] = " ".join(doc.xpath("//h1//text()")).lstrip("\n").split("\n")[0]
        data["time"]=get_time(doc)
        data["text"] = data["title"]+"\n"+data["time"]+"\n"+text
        return data

 
if __name__ == "__main__":
    args = get_args()
    data = main(args.input_file)
    # print(data)
    filename=data["id"]
    if len(filename)>200:
       filename=filename[:200] 
    if data["text"] !=" ":
         write_to_json(data, filename, extension="json", out_dir=args.out_dir)
         print('"' + change_extension(filename, ex=".json") + '"')



