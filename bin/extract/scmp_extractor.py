from lxml import etree
import re,argparse
from utils import remove_path
from utils import dump_to_json
from utils import write_to_json
from utils import change_extension
from datetime import datetime 

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', help="Path to input file")
    parser.add_argument('--out_dir', help="Path to output folder")
    args = parser.parse_args()
    return args

def main(args):
    filename=args.input_file
    with open(filename, "r",encoding="utf-8") as f:
        html_string = f.read()
    data = {}
    data["id"] = filename

    htmlparser = etree.HTMLParser(remove_comments=True)
    doc = etree.HTML(html_string, htmlparser)
    # Add time and title
    data["title"]=" ".join(doc.xpath('//h1/text()'))
    time=" ".join(doc.xpath('//div[@itemprop="dateCreated"]//text()'))
    time=re.sub("PUBLISHED : ","",time)
    time= datetime.strptime(time,"%A, %d %B, %Y, %H:%M%p").strftime("%Y-%m-%d") if len(time)>5 else ''
    if not time:
        node=doc.xpath('//meta[@property="article:published_time"]')
        if node: 
            time=re.sub("\+[0-9].*","",node[0].get("content"))
            time=datetime.strptime(time,"%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d") if len(time)>5 else ''

    data["time"]=time
    updated_time=" ".join(doc.xpath('//div[@itemprop="dateModified"]//text()'))
    updated_time=re.sub("UPDATED : ","",updated_time)
    updated_time=datetime.strptime(updated_time,"%A, %d %B, %Y, %H:%M%p").strftime("%Y-%m-%d") if len(updated_time)>5 else ''
    if updated_time:
        data["updated_time"]=updated_time

    text=" ".join([x for x in doc.xpath('//div//p/text()') if not x.lower().startswith("you are signed")])
    data["text"] = "\n".join([data["title"],data["time"],updated_time,text])
    # data = dump_to_json(data)
    return data

if __name__ == "__main__":
    args = get_args()
    data = main(args)
    # print(data)
    if len(data["id"])>200:
        data["id"]=data["id"][:200] 
    write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
    print('"' + change_extension(data["id"], ex=".json") + '"')