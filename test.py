from utils import *
# from TPL import TplItem, TPL, process_slot_info
from TPL_v2 import TplItem
import sys


def test_save_jsons_into_xlsx():
    xlsx_path = "./test.xlsx"
    json_lst = [
        {"name": "zhan0", "age": 10, "address": "安华里0"},
        {"name": "zhan1", "age": 11, "address": "安华里1"},
        {"name": "zhan2", "age": 12, "address": "安华里2"},
        {"name": "zhan2", "age": 12, "address": "安华里2"},
    ]

    # save_jsons_into_xlsx(xlsx_path=xlsx_path, json_lst=json_lst, sheet_name="信息统计")

    lst = [{"tmp": [1, 2, 3], "tmp2": ["1", "2", "3"]}]
    save_jsons_into_xlsx(json_lst=lst, xlsx_path="/Users/zhanzq/Downloads/test-tmp.xlsx")

    return


def test_load_jsons_from_xlsx():
    xlsx_path = "./test.xlsx"
    json_lst = load_jsons_from_xlsx_v2(xlsx_path=xlsx_path, sheet_name="信息统计")["信息统计"]
    print(json_lst)

    return


def test_tpl_analysis(version="v1"):
    tpl_path = "/Users/zhanzq/Downloads/intent_to_command_with_param_{}.xlsx".format(version)
    tpl_dct = load_jsons_from_xlsx_v2(xlsx_path=tpl_path)
    car_tp = "E38"
    conditions = dict()
    perception_data = dict()
    branch_info = dict()
    intent_info = dict()
    for car_type, tpl_items in tpl_dct.items():
        if car_tp and car_tp != car_type:
            continue
        for i, tpl_item in enumerate(tpl_items):
            tpl_item = TplItem(tpl_item=tpl_item)
            for key, val in tpl_item.data.items():
                perception_data[key] = perception_data.get(key, 0) + val
            for key, val in tpl_item.conditions.items():
                conditions[key] = conditions.get(key, 0) + val
            domain = tpl_item.domain
            branch = tpl_item.branch.split("=")[0]
            if branch != "" and branch != "default":
                if domain in branch_info:
                    branch_info[branch].add(domain)
                else:
                    branch_info[branch] = set([domain])

            intent = tpl_item.intent
            if intent not in intent_info:
                intent_info[intent] = 1
            else:
                intent_info[intent] += 1

    data_lst = [{"感知点": key, "频率": val} for key, val in perception_data.items()]
    data_lst.sort(key=lambda it: -it["频率"])
    save_jsons_into_xlsx(json_lst=data_lst, xlsx_path="/Users/zhanzq/Downloads/tpl_info_0324.xlsx", sheet_name="E38感知点信息")

    cond_lst = [{"判断条件": key, "频率": val} for key, val in conditions.items()]
    cond_lst.sort(key=lambda it: -it["频率"])
    save_jsons_into_xlsx(json_lst=cond_lst, xlsx_path="/Users/zhanzq/Downloads/tpl_info_0324.xlsx", sheet_name="E38判断条件信息")

    branch_lst = [{"槽位": key, "domain_lst": ", ".join(list(val))} for key, val in branch_info.items()]
    save_jsons_into_xlsx(json_lst=branch_lst, xlsx_path="/Users/zhanzq/Downloads/tpl_info_0324.xlsx", sheet_name="E38槽位信息")

    cond_lst = [{"intent": key, "频率": val} for key, val in intent_info.items()]
    cond_lst.sort(key=lambda it: -it["频率"])
    save_jsons_into_xlsx(json_lst=cond_lst, xlsx_path="/Users/zhanzq/Downloads/tpl_info_0324.xlsx", sheet_name="E38意图信息")

    # tpl_v4 = TPL(tpl_xlsx_path=tpl_v4_path)
    # tpl_v4.analysis_tpl_data(version="v4", car_type="E38")

    # tpl_pre_path = "/Users/zhanzq/github/xp-car-nlu/tools/gen/config/intent_to_command_with_param_pre.xlsx"
    # tpl_pre = TPL(tpl_xlsx_path=tpl_pre_path)
    # tpl_pre.analysis_tpl_data(version="pre", car_type="E38")


if __name__ == "__main__":
    # test_save_jsons_into_xlsx()
    # test_load_jsons_from_xlsx()
    # test_tpl_analysis(version="merged-pre-0401")

    # process_slot_info()

    # from TPL import parse_perceptual_data, get_from_adjust_info
    # data_dct = parse_perceptual_data(perceptual_data_path="/Users/zhanzq/Downloads/感知点汇总.xlsx")
    # res = get_from_adjust_info()
    #
    # codes = "tts('hello');"
    #
    # param_dct = TplItem.get_param_dct(format_codes=codes)
    # print(param_dct)
    # for cond in []:
    #     new_cond = TplItem.convert_cond_to_exact_info(cond, param_dct)
    #     print("convert {} to {}".format(cond, new_cond))

    revert_js_from_xlsx(js_path="/Users/zhanzq/Downloads/tpl_js_0402", xlsx_path="/Users/zhanzq/Downloads/intent_to_command_with_param_merged-0402.xlsx")
    revert_js_from_xlsx(js_path="/Users/zhanzq/Downloads/tpl_js_0420", xlsx_path="/Users/zhanzq/Downloads/intent_to_command_with_param_merged-0420.xlsx")

