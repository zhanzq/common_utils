# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# email : zhanzhiqiang09@126.com 
# date  : 2022/6/6
#

import os
import json
from utils import time_cost


@time_cost
def save_to_jsonl(json_lst: list, jsonl_path: str):
    """
    save json list into file, each line contains a dumped json object
    :param json_lst: list of json object
    :param jsonl_path: file path to store json objects, usually endswith ".jsonl"
    :return:
    """
    with open(jsonl_path, "w") as writer:
        for json_obj in json_lst:
            json_obj = {key: val for key, val in json_obj.items() if key or val}
            try:
                writer.write("{}\n".format(json.dumps(json_obj, ensure_ascii=False)))
            except Exception as e:
                print(e)


@time_cost
def load_from_jsonl(jsonl_path: str):
    """
    load json list from file, each line contains a dumped json object
    :param jsonl_path: type: str, file path storing json objects, usually endswith ".jsonl"
    :return: json object list
    """
    json_lst = []
    with open(jsonl_path, "r") as reader:
        for line in reader:
            try:
                json_obj = json.loads(line)
                json_lst.append(json_obj)
            except Exception as e:
                print(e)

    return json_lst


@time_cost
def save_to_json(json_obj: dict, json_path: str):
    """
    save json object into file
    :param json_obj: json object to store
    :param json_path: file path to store json object, usually endswith ".json"
    :return:
    """
    with open(json_path, "w") as writer:
        try:
            json.dump(json_obj, writer, ensure_ascii=False, indent=4)
        except Exception as e:
            print(e)


@time_cost
def load_from_json(json_path: str):
    """
    load json object from file
    :param json_path: type: str, file path storing json objects, usually endswith ".jsonl"
    :return: json object
    """
    json_obj = None
    if not os.path.exists(json_path):
        return None

    with open(json_path, "r") as reader:
        try:
            json_obj = json.load(reader)
        except Exception as e:
            print(e)

    return json_obj


def save_to_tsv(json_lst: list, tsv_path: str):
    """
    save json list into file, each line contains a dumped json object
    :param json_lst: list of json object
    :param tsv_path: file path to store json objects, usually endswith ".tsv"
    :return:
    """
    with open(tsv_path, "w") as writer:
        col_name_lst = [it for it in json_lst[0].keys()]
        writer.write("\t".join(col_name_lst) + "\n")
        for json_obj in json_lst:
            try:
                out_line = "\t".join([json_obj[key] for key in col_name_lst])
                writer.write(out_line + "\n")
            except Exception as e:
                print(e)


def load_from_tsv(tsv_path: str):
    """
    load json list from file, each line contains a dumped json object
    :param tsv_path: type: str, file path storing json objects, usually endswith ".tsv"
    :return: json object list
    """
    json_lst = []
    with open(tsv_path, "r") as reader:
        col_name_lst = reader.readline().strip().split("\t")
        for line in reader:
            try:
                values = line.strip().split("\t")
                json_obj = {key: val for key, val in zip(col_name_lst, values)}
                json_lst.append(json_obj)
            except Exception as e:
                print(e)

    return json_lst
