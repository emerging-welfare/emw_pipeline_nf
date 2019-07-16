from goose import Goose
from utils import remove_path # !!!
from utils import write_to_json # !!!

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help="Path to input file")
    parser.add_argument('out_dir', help="Path to output directory. Must contain '/' at the end.")
    args = parser.parse_args()
    return args

def main(args):
    filename = args.input_file
    with open(filename, "rb") as f:
        html_string = f.read()

    filename = remove_path(filename)
    g = Goose()
    article = g.extract(raw_html=html_string)
    data["text"] = text
    data["id"] = filename
    write_to_json(data, args.out_dirs + filename + ".json")

if __name__ == "__main__":
    args = get_args()
    main(args)
