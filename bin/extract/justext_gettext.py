import argparse
import justext
from utils import remove_path
from utils import dump_to_json
from utils import write_to_json
from utils import change_extension
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', help="Path to input file")
    parser.add_argument('--source_lang', help="Language of the source article.", default="English") # Need to be in list of languages supported in justext stoplist.
    parser.add_argument('--out_dir', help="Path to output folder")    
    args = parser.parse_args()
    return args

def main(args):
    filename = args.input_file
    with open(filename, "rb") as f:
        html_string = f.read()

    filename = remove_path(filename)
    text = ""
    paragraphs = justext.justext(html_string,justext.get_stoplist(args.source_lang))
    for paragraph in paragraphs:
        if not paragraph.is_boilerplate:
            text = text + paragraph.text + "\n"

    data = {}
    data["text"] = text
    data["id"] = filename
    #data = dump_to_json(data)
    return data

if __name__ == "__main__":
    args = get_args()
    data = main(args)
    #print(data)
    write_to_json(data, data["id"], extension="json", out_dir=args.out_dir)
    print('"' + change_extension(data["id"], ex=".json") + '"')
