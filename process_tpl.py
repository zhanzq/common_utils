# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# email : zhanzhiqiang09@126.com 
# date  : 2022/3/9
#

# generate nlg_id_info.txt config file
import os
import re

from text_io.excel import load_json_list_from_xlsx, save_json_list_into_xlsx
from text_io.txt import load_from_jsonl, save_to_jsonl, load_from_json, save_to_json

from utils import format_string
from TPL import TPL, TplItem


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


def add_param_into_tpl(tpl):
    return tpl


def add_param_into_nlg(tpl_xlsx_path, car_type="E38", version="0420"):
    base_json_dct = load_json_list_from_xlsx(tpl_xlsx_path)
    new_tpl_xlsx_path = "/Users/zhanzq/Downloads/intent_to_command_with_param-{}-format.xlsx".format(version)
    for car_tp, base_json_lst in base_json_dct.items():
        if car_tp == car_type:
            merged_json_lst = []
            for base_it in base_json_lst:
                it = TplItem(base_it)
                it.add_param_into_nlg()
                base_it["antlr"] = it.tpl
                merged_json_lst.append(base_it)
            save_json_list_into_xlsx(xlsx_path=new_tpl_xlsx_path, json_lst=merged_json_lst, sheet_name=car_tp)
        else:
            save_json_list_into_xlsx(xlsx_path=new_tpl_xlsx_path, json_lst=base_json_lst, sheet_name=car_tp)


def load_command_dct(command_lst_path):
    """
    load command dict from Sheet Table_KG of command_list file, "command_list.xlsx"
    :param command_lst_path: command list file path
    :return: dict(), in format: {INTENT1: {"domain": DOMAIN1, "intent": INTENT1, "example": EXAMPLE1}}
    """

    command_lst = load_json_list_from_xlsx(xlsx_path=command_lst_path, sheet_names=["Table_KG"]).get("Table_KG")
    command_dct = {}
    for item in command_lst:
        intent = item["intent"]
        command_dct[intent] = {
            "domain": item["domain"],
            "intent": intent,
            "example": item["sample"],
        }

    return command_dct


def parse_tpl_data(car_type="E38", version="0420"):
    tpl_xlsx_path = "/Users/zhanzq/Downloads/intent_to_command_with_param-{}.xlsx".format(version)
    if not os.path.exists(tpl_xlsx_path):
        tpl_xlsx_path = "/Users/zhanzq/Downloads/intent_to_command_with_param_merged-0420.xlsx"
    tpl = TPL(tpl_xlsx_path=tpl_xlsx_path)
    tpl.analysis_tpl_data(version=version, car_type=car_type)


def process_nlg_id_info(car_type="E38", version="0420"):
    # 0. parse tpl xlsx file, generate tts_info file, and insert nlg_md5
    parse_tpl_data(car_type=car_type, version=version)


def main():
    version = "0627"
    process_nlg_id_info(car_type="E38", version=version)


if __name__ == "__main__":
    main()
