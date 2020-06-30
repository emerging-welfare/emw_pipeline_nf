import re
import json

def remove_path(filename):
    return re.search(r"[^\/]+$", filename).group(0)

def filename_to_url(filename):
    url = re.sub(r"___?", r"://", filename)
    url = re.sub(r"_", r"/", url)
    return url

def change_extension(filename, ex=""):
    #return re.sub("(\.html?|\.cms|\.ece\d?|\.json|)$", ex, filename)
    return re.sub("\.\w{1,}$",".json",filename)
def write_to_json(data, filename, extension=None, out_dir=""):
    if extension is not None:
        filename = change_extension(filename, ex="."+extension)
##    json.dump(data, open(out_dir + filename, "w", encoding="utf-8"), ensure_ascii=False, sort_keys=True)
    with open(out_dir + filename, "w", encoding="utf-8",errors='surrogatepass') as wr:
         json.dump(data,wr,ensure_ascii=False,sort_keys=True)
         wr.write('\n')

def read_from_json(fpath):
   json_content=""
   with open(fpath, "r", encoding="utf-8",errors='surrogatepass') as f:
        json_content=json.loads(f.readline())
   return json_content

def load_from_json(data):
    data = re.sub(r"\[QUOTE\]", r"'", data)
    #data = re.sub(r'\!', r'!', data)
    return json.loads(data, encoding="utf-8")

def dump_to_json(data, add_label=False):
    if add_label:
        doc_label = str(data["doc_label"])
    data = json.dumps(data, sort_keys=True)
    data = re.sub(r"'", r"[QUOTE]", data)
    #data = re.sub(r'!', r'\!', data)
    if add_label:
        data = data + "," + doc_label

    return data

def print_token_and_label(tokens, token_labels):
    for token,label in zip(tokens, token_labels):
        print("%s %s"%(token,label))

def postprocess(data):
    all_tokens = []
    # sent_count = 0
    all_token_labels = []

    for i, token in enumerate(data["tokens"]):
        if token == "SAMPLE_START":
            token_labels = []
            tokens = []
        elif token == "[SEP]":
            all_tokens.append(tokens)
            # if data["sent_labels"][sent_count] == 0: # If sentence's label is 0, ignore all predicted tokens and reset them to 'O' tag.
            #     token_labels = ["O"] * len(token_labels)

            all_token_labels.append(token_labels)
            # sent_count += 1
            token_labels = []
            tokens = []
        else:
            tokens.append(token)
            token_labels.append(data["token_labels"][i])

    all_token_labels.append(token_labels)
    all_tokens.append(tokens)
    data["token_labels"] = all_token_labels
    data["tokens"] = all_tokens
    return data

def json_to_folia(data):

    from pynlpl.formats import folia

    foliaset = "https://github.com/OsmanMutlu/rawtext/raw/master/protes1-Task.foliaset.xml"

    tokens = data["tokens"]
    token_labels = data["token_labels"]

    doc_id = change_extension(re.sub(r"%", r"-h6j7k8-", data["id"]))
    doc = folia.Document(id=doc_id, filename=doc_id+".folia.xml")

    doc.declare(folia.Entity, foliaset)
    metadata = doc.metadata
    metadata["filename"] = data["id"]
    if "title" in data.keys():
        metadata["title"] = data["title"]
    if "time" in data.keys():
        metadata["time"] = data["time"]
    if "place" in data.keys():
        metadata["place"] = data["place"]

    doc.metadata = metadata

    text = doc.add(folia.Text)
    paragraph = text.add(folia.Paragraph)

    for sent_num,sent in enumerate(tokens):
        sentence = paragraph.add(folia.Sentence)
        sentence.cls = str(data["sent_labels"][sent_num])

        for token in sent:
            sentence.add(folia.Word, token)

        token_spans = []
        token_span = []
        to_labels = []
        for j,token_label in enumerate(token_labels[sent_num]):

            if token_label == "O" and token_span:
                token_spans.append(token_span)
                to_labels.append(prev_token_label)
                token_span = []

            elif token_label.startswith("B-"):
                if not token_span:
                    token_span.append(j)
                else:
                    token_spans.append(token_span)
                    to_labels.append(prev_token_label)
                    token_span = [j]
                prev_token_label = token_label[2:]

            elif token_label.startswith("I-"):
                if not token_span:
                    token_span.append(j)
                else:
                    if prev_token_label == token_label[2:]:
                        token_span.append(j)
                    else:
                        token_spans.append(token_span)
                        to_labels.append(prev_token_label)
                        token_span = [j]
                prev_token_label = token_label[2:]

        for j,span in enumerate(token_spans):
            span = [doc[doc_id + ".text.1.p.1.s." + str(sent_num+1) + ".w." + str(x+1)] for x in span]
            span[0].add(folia.Entity, *span, cls=to_labels[j], set=foliaset, annotator="BERT", annotatortype="auto")

    doc.save()

    # ["id", "text","title","length","creation_time","last_update_time","temporal_tags"->span_list,"place_names"->object_list,"participants"->span_list,"organizers"->span_list,"targets"->span_list,"triggers"->span_list,"targets"->span_list]
