from lxml import etree
import re,argparse
from utils import remove_path
from utils import dump_to_json
from utils import write_to_json
from utils import change_extension

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
    filename = remove_path(filename)
    data["id"] = filename
    htmlparser = etree.HTMLParser(remove_comments=True)
    doc = etree.HTML(html_string, htmlparser)
    # Add time and title
    data["title"]=" ".join(doc.xpath('//table//div[@id="p_title"]/text()'))

    if not data["title"]:
        data["title"]= " ".join(doc.xpath('//*//h1//text()'))
    if not data["title"]:
        data["title"]= doc.xpath('//*//h2//text()')[0] if doc.xpath('//*//h2//text()') else ""
        if data["title"]:
            data["time"]=doc.xpath('//*//span//text()')[0] if doc.xpath('//*//span//text()') else ""
            data["text"]=" ".join([x.strip("\n \t") for x in doc.xpath('//*//p//text()')]).strip()
            data = dump_to_json(data)
            return data

    data["time"]=" ".join(doc.xpath('//h3//*[@id="p_publishtime"]/text()'))

    if not data["time"]:
        data["time"]=" ".join(doc.xpath('//table//div[@id="p_publishtime"]/text()'))
    if not data["time"]:
        _=doc.xpath('//*//h2//text()')
        data["time"]= _[0] if len(_)>0 else ""

    data["text"]=" ".join([x.strip() for x in doc.xpath('//table//*//div[@id="p_content"]//text()')[:-1]]).strip("[ ]")

    if not data["text"]:
        data["text"]=" ".join([x.strip() for x in doc.xpath('//*[@id="p_content"]//text()')[:-1]])
    if not data["text"]:
        data["text"]=" ".join([x.strip() for x in doc.xpath('*//div[@id="ivs_content"]/text()')]).strip("\n ")
    if not data["text"]:
        data["text"]=" ".join([x.strip("\n\t ") for x in doc.xpath('*//p/text()') if x.strip("\n\t |")])
    return data

if __name__ == "__main__":
    args = get_args()
    data = main(args)
    # print(data)
    if len(data["id"])>200:
        data["id"]=data["id"][:200] 
    print(args.out_dir)
    write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
    print('"' + change_extension(data["id"], ex=".json") + '"')