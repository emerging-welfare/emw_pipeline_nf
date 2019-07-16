import re
import json

def remove_path(filename):
    return re.search(r"[^\/]+$", filename).group(0)

def change_extension(filename, ex1, ex2):
    return re.sub(re.escape(ex1) + "$", ex2, filename)

def read_from_json(filename):
    try:
        data =  json.load(open(filename, "r", encoding="utf-8"))
    except:
        pass # Can be logged and handled

def write_to_json(data, filename):
    try:
        json.dump(data, open(filename, "w", encoding="utf-8"), ensure_ascii=False, sort_keys=True)
    except:
        pass # Can be logged and handled

    # ["id", "text","title","length","creation_time","last_update_time","temporal_tags"->span_list,"place_names"->object_list,"participants"->span_list,"organizers"->span_list,"targets"->span_list,"triggers"->span_list,"targets"->span_list]
