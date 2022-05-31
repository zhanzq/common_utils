# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# email : zhanzhiqiang09@126.com 
# date  : 2022/3/9
#

# generate nlg_id_info.txt config file
import os
import re

from utils import load_jsons_from_xlsx, save_jsons_into_xlsx, load_jsons_from_xlsx_v2, gen_id, save_to_json, \
    load_from_json
from utils import load_from_jsonl, save_to_jsonl
from utils import format_string
# from TPL import TPL, TplItem

from TPL_v2 import TPL, TplItem


def process_tts(text):
    if not text or text == "N/A" or text == "#N/A":
        return []
    else:
        lst = re.split('\n|\d\. |/|\|', text)
        lst = [item.strip() for item in lst if item.strip()]
        return lst


def process_short_tts(short_auto, short_manual):
    lst = process_tts(short_auto)
    if not lst:
        return process_tts(short_manual)
    else:
        return lst


def cell_contains(text, st):
    if not text or text == "N/A" or text == "#N/A":
        return False
    else:
        for candidate in st:
            if candidate in text:
                return True

        return False


def get_config_item(item):
    can_exe_st = {"Action 反馈 - 执行了", "Action 反馈 - 正在执行", "Action 反馈 - 已是该状态", "Content 播报"}
    can_omit_st = {"省略为音效"}

    domain = item["Domain"]
    intent = item["Intent"] or ""
    slot = item["branch"] or "default"
    condition = item["condition"] or ""
    nlg_md5 = item["nlg_md5"]
    nlg_id = item["NLG ID"]
    can_omit = item["NLG是否可省略"] in can_omit_st
    can_exe = cell_contains(item.get("NLG 类型 - 一级"), can_exe_st)
    short_auto = item["NLG（简略版） - 公式自动生成"]
    short_manual = item["NLG（简略版）"]

    long = item["NLG（详尽版）\n（用于多条回复堆积时指向清晰）"]

    short_lst = process_short_tts(short_auto, short_manual)
    long_lst = process_tts(long)

    if not short_lst:
        short_lst = long_lst

    config_item = {
        "domain": domain,
        "intent": intent,
        "slot": slot,
        "condition": condition,
        "nlg_md5": nlg_md5,
        "nlgId": nlg_id,
        "canOmit": can_omit,
        "canExe": can_exe,
        "shortResp": short_lst,
        "longResp": long_lst,
    }

    return config_item


def get_config_items(json_dct):
    items = []
    sheet_names = ["control（1231=289+942）", "ac（364=127+237）- 思然", "system（232=96+136）- 刘洁"]

    for sheet_name in sheet_names:
        print(format_string(sheet_name))
        num = 0
        json_lst = json_dct[sheet_name]
        short_auto_mp = {}
        short_manual_mp = {}
        long_mp = {}

        for idx, item in enumerate(json_lst):
            config_item = get_config_item(item)
            short_auto = item["NLG（简略版） - 公式自动生成"]
            short_manual = item["NLG（简略版）"]
            long = item["NLG（详尽版）\n（用于多条回复堆积时指向清晰）"]
            short_auto_mp[short_auto] = short_auto_mp.get(short_auto, 0) + 1
            short_manual_mp[short_manual] = short_manual_mp.get(short_manual, 0) + 1
            long_mp[long] = long_mp.get(long, 0) + 1

            if config_item["longResp"]:
                items.append(config_item)
                num += 1
        print("sheet: {}, num: {}".format(sheet_name, num))

        # print(short_auto_mp)
        # print(short_manual_mp)
        # print(long_mp)
    return items


def generate_nlg_id_info(nlg_id_info_path, nlg_xlsx_path):
    json_dct = load_jsons_from_xlsx_v2(xlsx_path=nlg_xlsx_path)
    items = get_config_items(json_dct)
    print("config items: {}\nexamples: \n{}".format(len(items), items[0]))
    save_to_jsonl(json_lst=items, jsonl_path=nlg_id_info_path)


def analysis_nlg_id_info(json_lst):
    tts_num = len(json_lst)
    nlg_md5_lst = [item["nlg_md5"] for item in json_lst]
    nlg_md5_num = len(nlg_md5_lst)
    res_obj = {
        "tts_num": tts_num,
        "nlg_md5_num": nlg_md5_num,
        "nlg_md5_st": set(nlg_md5_lst),
    }

    return res_obj


def diff_nlg_info(old_info, new_info):
    print(format_string("compare two version nlg_id info"))
    print("old tpl version info: ")
    for key, val in old_info.items():
        if key != "nlg_md5_st":
            print("{}: {}".format(key, val))
        else:
            print("{} num: {}".format(key, len(val)))

    print("new tpl version info: ")
    for key, val in new_info.items():
        if key != "nlg_md5_st":
            print("{}: {}".format(key, val))
        else:
            print("{} num: {}".format(key, len(val)))

    inter = old_info["nlg_md5_st"].intersection(new_info.get("nlg_md5_st"))
    print("two version tpl nlg_md5 intersection: {}".format(len(inter)))

    return


def get_valid_nlg_md5s(tts_info_v1_path, tts_info_v2_path, nlg_id_info_path):
    json_lst1 = load_from_jsonl(tts_info_v1_path)
    json_lst2 = load_from_jsonl(tts_info_v2_path)

    old_info = analysis_nlg_id_info(json_lst1)
    new_info = analysis_nlg_id_info(json_lst2)

    diff_nlg_info(old_info, new_info)

    inter = old_info["nlg_md5_st"].intersection(new_info["nlg_md5_st"])

    changed_intent_lst = dict()
    for item in json_lst1:
        nlg_md5 = item["nlg_md5"]
        intent = item["intent"]
        if nlg_md5 not in inter:
            changed_intent_lst[intent] = 1 + changed_intent_lst.get(intent, 0)

    print("changed intent distribution info:")
    lst = [(key, val) for key, val in changed_intent_lst.items()]

    lst.sort(key=lambda it: -it[1])
    for key, val in lst:
        print("{}: {}".format(key, val))
    json_lst4 = load_from_jsonl(nlg_id_info_path)
    nlg_id_mp = {}
    for item in json_lst4:
        nlg_id_mp[item["nlg_md5"]] = item

    valid_nlg_md5s = {}
    for item in json_lst4:
        nlg_id = item["nlgId"]
        nlg_md5 = item["nlg_md5"]
        if nlg_md5 in inter:
            valid_nlg_md5s[nlg_md5] = nlg_id
            inter.remove(nlg_md5)

    return valid_nlg_md5s


def generate_tts_changed_info(tts_info_path, tts_changed_info_path, valid_nlg_md5s):
    json_lst = load_from_jsonl(tts_info_path)

    out_lst = []
    for item in json_lst:
        out_lst.append({key: val for key, val in item.items()})
        if item["nlg_md5"] in valid_nlg_md5s:
            out_lst[-1]["changed"] = False
        else:
            out_lst[-1]["changed"] = True

    version = tts_info_path.split("_")[-1].split(".")[0]
    sheet_name = "E38_{}_changed".format(version)
    save_jsons_into_xlsx(xlsx_path=tts_changed_info_path, json_lst=out_lst, sheet_name=sheet_name)


def filter_invalid_nlg_id(format_code, valid_nlg_md5s=None):
    if not valid_nlg_md5s:
        return format_code, 0
    else:
        changed = 0
        lines = format_code.split("\n")
        out_lines = []
        for line in lines:
            if re.fullmatch(' *nlg\("(.*)"\);', line):
                nlg_md5 = re.findall(' *nlg\("(.*)"\);', line)[0]
                if nlg_md5 in valid_nlg_md5s:
                    line = line.replace(nlg_md5, valid_nlg_md5s.get(nlg_md5, "unk_id"))
                    out_lines.append(line)
                    changed += 1
            else:
                out_lines.append(line)

        return "\n".join(out_lines), changed


def merge_tpl(tts_info_path, base_tpl_path, merged_xlsx_path, valid_nlg_md5s=None, car_type="E38"):
    json_lst = load_from_jsonl(jsonl_path=tts_info_path)
    format_codes_dct = {}
    for tpl_item in json_lst:
        key = tpl_item["intent"] + (tpl_item["branch"] or "default")
        format_codes_dct[key] = tpl_item["format"]
    base_json_dct = load_jsons_from_xlsx(base_tpl_path)

    for car_tp, base_json_lst in base_json_dct.items():
        if car_tp == car_type:
            merged_json_lst = []
            changed_num = 0
            for item in base_json_lst:
                key = item["intent"] + (item["param"] or "default")
                if key in format_codes_dct:
                    format_code = format_codes_dct[key]
                    filtered_code, changed_i = filter_invalid_nlg_id(format_code, valid_nlg_md5s)
                    changed_num += changed_i
                    item["antlr"] = filtered_code

                merged_json_lst.append(item)
            print("total insert nlg: {}".format(changed_num))
            save_jsons_into_xlsx(xlsx_path=merged_xlsx_path, json_lst=merged_json_lst, sheet_name=car_tp)
        else:
            save_jsons_into_xlsx(xlsx_path=merged_xlsx_path, json_lst=base_json_lst, sheet_name=car_tp)


def merge_tpl_v2(tts_info_path, base_tpl_path, merged_xlsx_path, car_type="E38", version="0420"):
    sheet_name = "{}_{}_tid".format(car_type, version)
    json_lst = load_jsons_from_xlsx_v2(xlsx_path=tts_info_path, sheet_name=sheet_name)[sheet_name]
    format_codes_lst = []
    pre_key = None
    for tpl_item in json_lst:
        key = tpl_item["intent"] + (tpl_item["slot"] or "default")
        if pre_key != key:
            format_codes_lst.append(tpl_item)
        pre_key = key

    print("format_codes_lst: {}".format(len(format_codes_lst)))
    base_json_dct = load_jsons_from_xlsx(base_tpl_path)
    for car_tp, base_json_lst in base_json_dct.items():
        if car_tp == car_type:
            merged_json_lst = []
            print("car_type: {}, base_json_lst: {}".format(car_tp, len(base_json_lst)))
            i = 0
            for base_it in base_json_lst:
                if base_it["antlr"]:
                    base_it["antlr"] = format_codes_lst[i]["tpl"]
                    i += 1
                merged_json_lst.append(base_it)
            save_jsons_into_xlsx(xlsx_path=merged_xlsx_path, json_lst=merged_json_lst, sheet_name=car_tp)
        else:
            save_jsons_into_xlsx(xlsx_path=merged_xlsx_path, json_lst=base_json_lst, sheet_name=car_tp)


def add_param_into_tpl(tpl):
    return tpl


def add_param_into_nlg(tpl_xlsx_path, car_type="E38", version="0420"):
    base_json_dct = load_jsons_from_xlsx(tpl_xlsx_path)
    new_tpl_xlsx_path = "/Users/zhanzq/Downloads/intent_to_command_with_param-{}-format.xlsx".format(version)
    for car_tp, base_json_lst in base_json_dct.items():
        if car_tp == car_type:
            merged_json_lst = []
            for base_it in base_json_lst:
                it = TplItem(base_it)
                it.add_param_into_nlg()
                base_it["antlr"] = it.tpl
                merged_json_lst.append(base_it)
            save_jsons_into_xlsx(xlsx_path=new_tpl_xlsx_path, json_lst=merged_json_lst, sheet_name=car_tp)
        else:
            save_jsons_into_xlsx(xlsx_path=new_tpl_xlsx_path, json_lst=base_json_lst, sheet_name=car_tp)


def load_command_dct(command_lst_path):
    """
    load command dict from Sheet Table_KG of command_list file, "command_list.xlsx"
    :param command_lst_path: command list file path
    :return: dict(), in format: {INTENT1: {"domain": DOMAIN1, "intent": INTENT1, "example": EXAMPLE1}}
    """

    command_lst = load_jsons_from_xlsx(xlsx_path=command_lst_path, sheet_name="Table_KG").get("Table_KG")
    command_dct = {}
    for item in command_lst:
        intent = item["intent"]
        command_dct[intent] = {
            "domain": item["domain"],
            "intent": intent,
            "example": item["sample"],
        }

    return command_dct


def parse_nlg_info_from_tpl_item(tpl_item, command_dct):
    """
    check the tpl_item, whether all tts' have corresponding nlg_id
    :param tpl_item: in format: {"intent": INTENT, "param": PARAM, "command": COMMAND, "antlr": ANTLR}
    :param command_dct: dict,  in format: {INTENT1: {"domain": DOMAIN1, "intent": INTENT1, "example": EXAMPLE1}}
    :return: dict, in format {"intent": INTENT, "branch": BRANCH, "nlg_info": NLG_INFO, "example": EXAMPLE},
            NLG_INFO: {"全部", "部分", "没有"}
    """
    intent = tpl_item["intent"]
    branch = tpl_item.get("param") or "default"
    antlr = tpl_item["antlr"]
    format_codes = antlr.split("\n")

    tts_lst, nlg_lst = [], []
    for i, line in enumerate(format_codes):
        if line.lstrip().startswith("tts("):
            tts_lst.append((i, line))
        elif line.lstrip().startswith("nlg("):
            nlg_lst.append((i, line))

    nlg_info = "没有"
    if antlr and len(tts_lst) == len(nlg_lst):
        nlg_info = "全部"
    elif len(nlg_lst) > 0:
        nlg_info = "部分"

    ret_obj = {
        "intent": intent,
        "branch": branch,
        "nlg_info": nlg_info,
        "example": command_dct.get(intent, {}).get("example")
    }

    if intent not in command_dct:
        print("intent '{}' not in command_list file".format(intent))
    return ret_obj


def parse_nlg_info_from_xlsx(merged_xlsx_path, command_lst_path, tpl_nlg_info_path):
    """
    check all tpl_items in merged file, whether all tts' have corresponding nlg_id
    :param merged_xlsx_path: the merged tpl path, in xlsx format
    :param command_lst_path: command list file path
    :param tpl_nlg_info_path: output file path, in xlsx format, each line presents an item,
            in format {"intent": INTENT, "branch": BRANCH, "nlg_info": NLG_INFO, "example": EXAMPLE},
            sorted by nlg_info, intent and branch,
            NLG_INFO: {"全部", "部分", "没有"}
    """
    command_dct = load_command_dct(command_lst_path=command_lst_path)
    nlg_info_lst = []
    tpl_item_lst = load_jsons_from_xlsx(xlsx_path=merged_xlsx_path, sheet_name="E38")["E38"]
    valid_tts_num = 0
    invalid_tts_num = 0
    for tpl_item in tpl_item_lst:
        if not tpl_item["antlr"]:
            tpl_item["antlr"] = ""
        nlg_info = parse_nlg_info_from_tpl_item(tpl_item=tpl_item, command_dct=command_dct)
        nlg_info_lst.append(nlg_info)
        if nlg_info["nlg_info"] == "全部":
            valid_tts_num += len(re.findall("tts\(", tpl_item["antlr"]))
        else:
            invalid_tts_num += len(re.findall("tts\(", tpl_item["antlr"]))

    print("total valid tts num: {}".format(valid_tts_num))
    print("total invalid tts num: {}".format(invalid_tts_num))
    nlg_info_lst.sort(key=lambda it: (it["nlg_info"], it["intent"], it["branch"]))

    save_jsons_into_xlsx(xlsx_path=tpl_nlg_info_path, json_lst=nlg_info_lst, sheet_name="tpl_nlg_info")

    return nlg_info_lst


def generate_filtered_nlg_id_info(nlg_id_info_path, tpl_nlg_info_path, filtered_nlg_id_info_path):
    nlg_info_lst = load_jsons_from_xlsx(tpl_nlg_info_path, sheet_name="tpl_nlg_info")["tpl_nlg_info"]
    nlg_id_info_lst = load_from_jsonl(nlg_id_info_path)
    nlg_info_dct = {}
    for nlg_info in nlg_info_lst:
        intent = nlg_info["intent"]
        branch = nlg_info["branch"]
        key = str(intent) + str(branch)
        nlg_info_dct[key] = nlg_info

    filtered_nlg_id_info_lst = []
    for nlg_id_info in nlg_id_info_lst:
        intent = nlg_id_info["intent"]
        branch = nlg_id_info["branch"]
        key = str(intent) + str(branch)
        if key in nlg_info_dct and nlg_info_dct[key]["nlg_info"] == "全部":
            filtered_nlg_id_info_lst.append(nlg_id_info)

    save_jsons_into_xlsx(xlsx_path=filtered_nlg_id_info_path, json_lst=filtered_nlg_id_info_lst,
                         sheet_name="filtered_nlg_id_info")


def generate_filtered_nlg_id_info_by_intent(nlg_id_info_path, tpl_nlg_info_path, filtered_nlg_id_info_path):
    nlg_info_lst = load_jsons_from_xlsx(tpl_nlg_info_path, sheet_name="tpl_nlg_info")["tpl_nlg_info"]
    nlg_id_info_lst = load_from_jsonl(nlg_id_info_path)
    valid_intent_dct = {}
    for nlg_info in nlg_info_lst:
        intent = nlg_info["intent"]
        if nlg_info["nlg_info"] == "全部":
            valid_intent_dct[intent] = valid_intent_dct.get(intent, True)
        else:
            valid_intent_dct[intent] = False

    filtered_nlg_id_info_lst = []
    for nlg_id_info in nlg_id_info_lst:
        intent = nlg_id_info["intent"]
        if intent in valid_intent_dct and valid_intent_dct[intent]:
            filtered_nlg_id_info_lst.append(nlg_id_info)

    print("filter valid intent: {}".format(len([intent for intent in valid_intent_dct if valid_intent_dct[intent]])))
    print("filter valid tts: {}".format(len(filtered_nlg_id_info_lst)))
    save_jsons_into_xlsx(xlsx_path=filtered_nlg_id_info_path, json_lst=filtered_nlg_id_info_lst,
                         sheet_name="filtered_nlg_id_info_by_intent")


def compare_two_version_tts_info(old_version, new_version):
    old_tts_info_path = "/Users/zhanzq/Downloads/tts_info_E38_{}.jsonl".format(old_version)
    new_tts_info_path = "/Users/zhanzq/Downloads/tts_info_E38_{}.jsonl".format(new_version)
    old_tts_info_lst = load_from_jsonl(jsonl_path=old_tts_info_path)
    new_tts_info_lst = load_from_jsonl(jsonl_path=new_tts_info_path)

    print("old_tts_info_lst sz: {}".format(len(old_tts_info_lst)))
    print("new_tts_info_lst sz: {}".format(len(new_tts_info_lst)))
    print("keys in old_tts_info_lst: \n{}".format(list(old_tts_info_lst[0].keys())))
    print("keys in new_tts_info_lst: \n{}".format(list(new_tts_info_lst[0].keys())))

    for key in old_tts_info_lst[0].keys():
        print(format_string("compare key: {}".format(key)))
        diff_num = 0
        idx = 0
        for item1, item2 in zip(old_tts_info_lst, new_tts_info_lst):
            idx += 1
            if item1[key] != item2[key]:
                diff_num += 1
        #             if key in ["tts", "condition"]:
        #                 print(format_string("idx = {}".format(idx)))
        #                 print(item1[key])
        #                 print(item2[key])
        print("diff_num: {}".format(diff_num))

    return


def divide_labor(version):
    division_path = "/Users/zhanzq/Downloads/语音全局&可见即可说_需求汇总文档-0401.xlsx"
    json_dct = load_jsons_from_xlsx_v2(xlsx_path=division_path)
    division_dct = {}
    pre_name = None
    for sheet_name in ["车辆控制", "空调", "系统设置"]:
        json_lst = json_dct[sheet_name]
        for it in json_lst:
            intent = it["全局意图"]
            if not intent:
                continue
            else:
                intent = intent.split("\n")[0].strip()
            pre_name = it["分工"] or pre_name
            division_dct[intent] = pre_name
            if division_dct[intent] == "未分配":
                print("intent: {}, domain: {}".format(intent, sheet_name))

    tts_info_path = "/Users/zhanzq/Downloads/tts_info.xlsx"
    sheet_name = "E38_{}".format(version)
    intent_e38 = set()
    tts_info_lst = load_jsons_from_xlsx_v2(xlsx_path=tts_info_path, sheet_name=sheet_name)[sheet_name]
    for tts_info in tts_info_lst:
        intent = tts_info["intent"]
        if tts_info["domain"] in ["system", "ac", "control"]:
            intent_e38.add(intent)
        tts_info["分工"] = division_dct.get(intent)

    print(format_string("三领域的意图共计: {}".format(len(division_dct))))
    print(format_string("E38的领域意图共计: {}".format(len(intent_e38))))
    print(format_string("公共意图共计: {}".format(len(intent_e38.intersection(division_dct.keys())))))

    save_jsons_into_xlsx(xlsx_path=tts_info_path, sheet_name=sheet_name + "-分工", json_lst=tts_info_lst)


def convert_md5_to_tid_in_tpl(tpl, md5_to_tid):
    if not tpl:
        return tpl

    code_lines = tpl.split("\n")
    for i, line in enumerate(code_lines):
        if line.strip().startswith("nlg("):
            md5_or_tid = re.findall("nlg\([\"'](.*)[\"']\)", line)[0]
            if "_" not in md5_or_tid and md5_or_tid in md5_to_tid:
                line = line.replace(md5_or_tid, md5_to_tid[md5_or_tid])
                code_lines[i] = line
    return "\n".join(code_lines)


def get_max_nlg_id_and_update_reflect_dct(tpl, reflect_dct, domain):
    if not tpl:
        return 0

    code_lines = tpl.split("\n")
    max_nlg_id = 0
    for line in code_lines:
        if line.strip().startswith("nlg("):
            nlg_md5_or_id = re.findall("nlg\(\"(.*)\"\)", line)[0]
            if "_" in nlg_md5_or_id:
                nlg_id = int(nlg_md5_or_id.split("_")[-1])
                max_nlg_id = max(max_nlg_id, nlg_id)
            else:
                if nlg_md5_or_id not in reflect_dct:
                    reflect_dct[nlg_md5_or_id] = domain + "_N_"

    return max_nlg_id


def update_md5_to_tid(start_tid, md5_to_tid):
    for md5 in md5_to_tid:
        if not md5_to_tid[md5] or md5_to_tid[md5][-1] == '_':
            md5_to_tid[md5] = str(start_tid)
            start_tid += 1

    return


def insert_nlg_md5(tpl_xlsx_path, car_type="E38", version="0420"):
    item_dct = load_jsons_from_xlsx_v2(xlsx_path=tpl_xlsx_path)
    tpl_with_md5_xlsx_path = "/Users/zhanzq/Downloads/intent_to_command_with_param_{}-md5.xlsx".format(version)
    for sheet_name, item_lst in item_dct.items():
        if sheet_name != car_type:
            save_jsons_into_xlsx(xlsx_path=tpl_with_md5_xlsx_path, json_lst=item_lst, sheet_name=sheet_name)
        else:
            out_lst = []
            for item in item_lst:
                if item["antlr"]:
                    tpl_item = TplItem(item)
                    # tpl_item.insert_nlg_md5_v2()
                    item["antlr"] = tpl_item.tpl
                out_lst.append(item)

            save_jsons_into_xlsx(xlsx_path=tpl_with_md5_xlsx_path, json_lst=out_lst, sheet_name=sheet_name)

    return


def convert_md5_to_tid(car_type="E38", version="0420", md5_to_tid_path=None):
    if not md5_to_tid_path:
        md5_to_tid_path = "/Users/zhanzq/Downloads/md5_to_tid.json"
    md5_to_tid = load_from_json(json_path=md5_to_tid_path) or {}

    tts_info_path = "/Users/zhanzq/Downloads/tts_info.xlsx"
    sheet_name = "{}_{}_md5".format(car_type, version)
    tts_info_lst = load_jsons_from_xlsx_v2(xlsx_path=tts_info_path, sheet_name=sheet_name)[sheet_name]
    max_tid = 0
    for tts_info in tts_info_lst:
        md5 = tts_info.get("nlg_md5")
        tid = tts_info.get("nlg_id")
        if md5 not in md5_to_tid:
            md5_to_tid[md5] = tid
        elif tid and tid != md5_to_tid[md5]:
            print("conflicting info between md5_to_tid and tpl, md5: {}, \ntid_in_conf: {}, \ntid_in_tpl : {}"
                  .format(md5, md5_to_tid[md5], tid))
        if tid and not tid.startswith("PN"):
            tid_idx = int(tid.split("_")[-1])
            max_tid = max(max_tid, tid_idx)

    update_md5_to_tid(max_tid+1, md5_to_tid)

    print(format_string("cur version max tid: {}".format(max_tid)))
    for tts_info in tts_info_lst:
        md5 = tts_info.get("nlg_md5")
        domain = tts_info.get("domain")
        tid = tts_info.get("nlg_id")
        if not tid:
            tid = md5_to_tid[md5]
            if "_N_" not in tid:
                tid = "{}_N_{}".format(domain, tid)
            md5_to_tid[md5] = tid
            tts_info["nlg_id"] = tid
        tpl = tts_info.get("tpl", tts_info.get("format"))
        tpl = convert_md5_to_tid_in_tpl(tpl, md5_to_tid)
        tts_info["tpl"] = tpl

    save_to_json(json_obj=md5_to_tid, json_path=md5_to_tid_path)
    sheet_name = "{}_{}_tid".format(car_type, version)
    save_jsons_into_xlsx(xlsx_path=tts_info_path, sheet_name=sheet_name, json_lst=tts_info_lst)


def parse_tpl_data(car_type="E38", version="0420"):
    tpl_xlsx_path = "/Users/zhanzq/Downloads/intent_to_command_with_param-{}.xlsx".format(version)
    if not os.path.exists(tpl_xlsx_path):
        tpl_xlsx_path = "/Users/zhanzq/Downloads/intent_to_command_with_param_merged-0420.xlsx"
    tpl = TPL(tpl_xlsx_path=tpl_xlsx_path)
    tpl.analysis_tpl_data(version=version, car_type=car_type)
    sheet_name = "{}_{}_md5".format(car_type, version)
    json_lst = load_jsons_from_xlsx_v2("/Users/zhanzq/Downloads/tts_info.xlsx", sheet_name=sheet_name)[sheet_name]
    bad_conds = []
    for item in json_lst:
        if not item["未成功解析的判断条件"]:
            continue
        for bad_cond in item["未成功解析的判断条件"]:
            perceptual_data = re.findall("\w+\.[\w\.]+", bad_cond)
            if perceptual_data:
                perceptual_data = perceptual_data[0]
            else:
                perceptual_data = None
            bad_conds.append(
                {"未成功解析的判断条件": bad_cond, "domain": item["domain"], "intent": item["intent"], "感知点": perceptual_data})
    bad_tpl_info_path = "/Users/zhanzq/Downloads/un_parsed_tpl_info_{}_{}.xlsx".format(car_type, version)
    save_jsons_into_xlsx(xlsx_path=bad_tpl_info_path, sheet_name="未成功解析的判断条件", json_lst=bad_conds)


def process_nlg_id_info(car_type="E38", version="0420"):
    # 0. parse tpl xlsx file, generate tts_info file, and insert nlg_md5
    parse_tpl_data(car_type=car_type, version=version)

    # # 1. get nlg_id_info, save into jsonl file
    nlg_id_info_path = "/Users/zhanzq/Downloads/nlg_id_info_v2.txt"
    nlg_xlsx_path = "/Users/zhanzq/Downloads/语音全局NLG需求汇总文档_v2.xlsx"
    # generate_nlg_id_info(nlg_id_info_path=nlg_id_info_path, nlg_xlsx_path=nlg_xlsx_path)
    #

    # 4. generate filtered nlg_id info file, and provide it to testers to validate functions
    command_lst_path = "/Users/zhanzq/Downloads/command_list_pre.xlsx"
    tpl_nlg_info_path = "/Users/zhanzq/Downloads/tpl_nlg_info_pre.xlsx"
    # parse_nlg_info_from_xlsx(merged_xlsx_path=merged_xlsx_path, command_lst_path=command_lst_path,
    #                          tpl_nlg_info_path=tpl_nlg_info_path)

    # filtered_nlg_id_info_path = "/Users/zhanzq/Downloads/filtered_nlg_id_info_pre.xlsx"
    # generate_filtered_nlg_id_info(nlg_id_info_path=nlg_id_info_path, tpl_nlg_info_path=tpl_nlg_info_path,
    #                               filtered_nlg_id_info_path=filtered_nlg_id_info_path)

    filtered_nlg_id_info_path = "/Users/zhanzq/Downloads/filtered_nlg_id_info.xlsx"
    # generate_filtered_nlg_id_info_by_intent(nlg_id_info_path=nlg_id_info_path, tpl_nlg_info_path=tpl_nlg_info_path,
    #                                         filtered_nlg_id_info_path=filtered_nlg_id_info_path)

    # 7. add division of labor info
    # divide_labor(version=version)

    # 8. replace nlg_md5 with nlg_id
    convert_md5_to_tid(car_type=car_type, version=version)

    # 9. merge tpl
    tts_info_path = "/Users/zhanzq/Downloads/tts_info.xlsx"
    base_tpl_path = "/Users/zhanzq/Downloads/intent_to_command_with_param-{}.xlsx".format(version)
    merged_xlsx_path = "/Users/zhanzq/Downloads/intent_to_command_with_param-{}-merged.xlsx".format(version)
    merge_tpl_v2(tts_info_path=tts_info_path, base_tpl_path=base_tpl_path,
                 merged_xlsx_path=merged_xlsx_path, car_type=car_type, version=version)

    # 10. add param into nlg()
    tpl_xlsx_path = "/Users/zhanzq/Downloads/intent_to_command_with_param-{}-merged.xlsx".format(version)
    add_param_into_nlg(tpl_xlsx_path=tpl_xlsx_path, car_type=car_type, version=version)


if __name__ == "__main__":
    version = "0523"
    process_nlg_id_info(car_type="E38", version=version)
