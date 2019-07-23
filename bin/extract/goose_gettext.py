import argparse
from goose import Goose
from utils import remove_path
from utils import dump_to_json

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', help="Path to input file")
    args = parser.parse_args()
    return args

def main(args):
    filename = args.input_file
    with open(filename, "rb") as f:
        html_string = f.read()

    filename = remove_path(filename)
    g = Goose()
    article = g.extract(raw_html=html_string)
    data = {}
    data["text"] = text
    data["id"] = filename
    data = dump_to_json(data)
    return data

if __name__ == "__main__":
    args = get_args()
    data = main(args)
    print(data)
