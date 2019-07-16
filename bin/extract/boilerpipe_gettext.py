from boilerpipe.extract import Extractor
from ..utils import remove_path
from ..utils import dump_to_json

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help="Path to input file")
    parser.add_argument('no_byte', help="If html file needs to be read with 'rb' tag.", action="store_true") # Only pass for scmp articles
    args = parser.parse_args()
    return args

def main(args):
    filename = args.input_file
    if args.no_byte:
        with open(filename, "r") as f:
            html_string = f.read()
    else:
        with open(filename, "rb") as f:
            html_string = f.read()

    filename = remove_path(filename)
    extractor = Extractor(extractor='ArticleExtractor', html=html_string)
    extracted_text = extractor.getText()
    data["text"] = extracted_text
    data["id"] = filename
    data = dump_to_json(data)
    return data, args.input_file

if __name__ == "__main__":
    args = get_args()
    return main(args)
