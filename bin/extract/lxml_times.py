from lxml import etree
import re,argparse
from utils import remove_path
#from utils import dump_to_json
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
def get_time(doc):
    l=len(doc.xpath('//span[contains(@class,"time_cptn")]//span'))
    if l>0:
        if l==1:
            time = " ".join(doc.xpath('//span[contains(@class,"time_cptn")]//span/text()'))
            return time
        else:
            time = " ".join(doc.xpath('//span[contains(@class,"time_cptn")]//span[{0}]/text()'.format(l-1)))
            if time:
                if "Updated:" in time.split():
                    time= " ".join(time.split("Updated:")[1:]).lstrip(":").rstrip(":").strip()
                #"time" = time.split("|")[-1].strip()
            return time 
    time=doc.xpath('//span[contains(@class,"time_cptn")]/text()')
    if time:
        return time[0].split("|")[-1].strip()
    return " "

def main(args):
        filename=args.input_file; unvaild_pages=set(["photo-stories","recipes","bollywood","slideshow","relationships","bollywood-unknown_photo-stories"])
        if set.intersection(set(remove_path(filename).split("_")), unvaild_pages):
            return {"id":remove_path(filename),"text":" ","title":" ","time":" "}
        with open(filename, "rb") as f:
            html_string = f.read()

        stoplist = ["... contd.", "Please read our terms of use before posting comments"]
        filename = remove_path(filename)
        data = {}
        data["id"] = filename

        htmlparser = etree.HTMLParser(remove_comments=True)
        doc = etree.HTML(html_string, htmlparser)
        node = doc.xpath('//div[contains(@class, "Normal")]')
        if node:
            text = ""
            for s in [re.sub(r" {2,}|\n|\t|\r", r"", x) for x in doc.xpath('//div[contains(@class, "Normal")]/text()')]:
                if s:
                    text += s
                    break
            text += stringify_children(node[0])
        else:
    #        print("text is empyt",filename)
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
        data["title"] = " ".join(doc.xpath("//h1/text()"))
        data["time"]=get_time(doc)
        data["text"] = data["title"]+"\n"+data["time"]+"\n"+text
    # data = dump_to_json(data)
        return data
    
if __name__ == "__main__":
    args = get_args()
    data = main(args)
    # print(data)
    filename=data["id"]
    if len(filename)>200:
       filename=filename[:200] 
    write_to_json(data, filename, extension="json", out_dir=args.out_dir)
    print('"' + change_extension(filename, ex=".json") + '"')
