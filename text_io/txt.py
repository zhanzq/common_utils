# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# email : zhanzhiqiang09@126.com 
# date  : 2022/6/6
#

import os
import json
from common_utils.utils import time_cost

import copy


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
            print("save {} records into json file".format(len(json_obj)))
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


def _update_json_obj_by_var_path(json_obj: dict, domains: list, val) -> dict:
    """
    update json object by given path and val
    :param json_obj: the input json to update
    :param domains: the given path, e.g. ["a", "b-1", "c"] stands for it["a"]["b"][1]["c"]
    :param val: the value to set
    :return:
    """
    domain = domains[0]
    if "-" not in domain:
        if len(domains) == 1:
            json_obj[domain] = val
        else:
            sub_json = json_obj.get(domain, {})
            json_obj[domain] = _update_json_obj_by_var_path(sub_json, domains[1:], val)
    else:
        domain, idx = domain.split("-")
        idx = int(idx)
        if domain not in json_obj:
            json_obj[domain] = []           # in this case, the val should be None

        if len(domains) > 1:
            if len(json_obj[domain]) <= idx:
                json_obj[domain].append({})
            sub_json = json_obj[domain][idx]
            out_obj = _update_json_obj_by_var_path(sub_json, domains[1:], val)
            json_obj[domain][idx].update(out_obj)
        else:
            if val is not None:     # not an empty list
                json_obj[domain].append(val)

    return json_obj


def has_valid_value(input_obj):
    if isinstance(input_obj, dict):
        for _, _val in input_obj.items():
            if _val:
                return True
    elif isinstance(input_obj, list):
        for _val in input_obj:
            if _val:
                return True

    return False


def clean_json_obj(json_obj):
    """
    clean the null values in json_obj, e.g. ["a", "", None] ==> ["a"]
    :param json_obj: the input json to clean
    :return:
    """
    if not isinstance(json_obj, dict):
        return json_obj
    elif not has_valid_value(json_obj):
        return {}

    keys = list(json_obj.keys())
    for key in keys:
        val = json_obj[key]
        if isinstance(val, dict):
            tmp_dct = clean_json_obj(val)
            if not has_valid_value(tmp_dct):
                json_obj[key] = {}
        elif isinstance(val, list):
            lst = [clean_json_obj(it) for it in val]
            lst = [it for it in lst if it]
            if not has_valid_value(lst):
                json_obj[key] = []
            else:
                json_obj[key] = lst
    return json_obj


def clean_null_vals_in_json_obj(json_obj):
    """
    clean the null values in json_obj, e.g. ["a", "", None] ==> ["a"]
    :param json_obj: the input json to clean
    :return:
    """
    if not isinstance(json_obj, dict):
        return json_obj
    elif not has_valid_value(json_obj):
        return {}

    keys = list(json_obj.keys())
    for key in keys:
        val = json_obj[key]
        if val is None:
            json_obj.pop(key)
        elif isinstance(val, dict):
            tmp_dct = clean_null_vals_in_json_obj(val)
            if not has_valid_value(tmp_dct):
                json_obj[key] = {}
            else:
                json_obj[key] = tmp_dct
        elif isinstance(val, list):
            lst = [clean_null_vals_in_json_obj(it) for it in val]
            lst = [it for it in lst if it]
            if not has_valid_value(lst):
                json_obj[key] = []
            else:
                json_obj[key] = lst
    return json_obj


def fold_json_obj(json_obj: dict) -> dict:
    """
    fold a flat json object, e.g. {"a.b": 10} ==> {"a": {"b": 10}}
    :param json_obj: the input json to process
    :return:
    """
    out_obj = {}
    for key, val in json_obj.items():
        if val and isinstance(val, str) and val[0] == '"' and val[-1] == '"':
            val = val[1:-1]
        elif isinstance(val, type):
            val = val.__name__
        domains = key.split(".")
        _update_json_obj_by_var_path(out_obj, domains, val)

    clean_obj = clean_json_obj(out_obj)
    return copy.deepcopy(clean_obj)


def is_num(num):
    """
    check a string is numeric or not
    :param num: the input string to check
    :return:
    """
    try:
        float(num)
        return True
    except ValueError:
        return False


def flatten_json_obj(json_obj: dict) -> dict:
    """
    flatten json object, e.g. {"a": {"b": 10}} ==> {"a.b": 10}
    :param json_obj: the input json to process
    :return:
    """
    out_obj = {}
    for key, val in json_obj.items():
        if not val:
            if isinstance(val, str):
                val = '""'
            out_obj[key] = val
            continue
        if isinstance(val, list):
            sub_json = {f"{key}-{idx}": _val for idx, _val in enumerate(val)}
            if not sub_json:
                out_obj[f"{key}-0"] = None
                continue
            tmp_dct = flatten_json_obj(sub_json)
            for _key, _val in tmp_dct.items():
                out_obj[_key] = _val
        elif isinstance(val, dict):
            tmp_dct = flatten_json_obj(val)
            for _key, _val in tmp_dct.items():
                out_obj[f"{key}.{_key}"] = _val
        else:
            if isinstance(val, str) and is_num(val):
                val = f"\"{val}\""
            out_obj[key] = val

    return out_obj
