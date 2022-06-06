# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# email : zhanzhiqiang09@126.com 
# date  : 2022/6/6
#
import os
import re
import traceback

from utils import time_cost, format_string
from io.excel import load_json_list_from_xlsx, save_json_list_into_xlsx


# 获取antlr中所有可能的预定义方法
def get_candidate_functions(code):
    if not code:
        return set()
    function_ptn = "(\w+)\("
    return set(re.findall(function_ptn, code))


def get_all_pre_defined_functions(tpl_xlsx_path):
    json_dct = load_json_list_from_xlsx(tpl_xlsx_path)
    st = set()
    for car_type, json_lst in json_dct.items():
        for item in json_lst:
            tmp = get_candidate_functions(item["antlr"])
            st = st.union(tmp)

    for key in st:
        print("\"function {}() ".format(key) + "{ }\",")


# all methods in js function <---> json object
def get_pre_defined_function():
    function_lst = [
        "function data(key) { }",
        "function param(name) { }",
        "function delay(time) { }",
        "function cmd(command) { }",
        "function tts(text) { }",
        "function eqMethod(left, right) { }",
        "function neqMethod(left, right) { }",
        "function ltMethod(left, right) { }",
        "function geMethod(left, right) { }",
        "function gtMethod(left, right) { }",
        "function and(left, right) { }",
        "function or(left, right) { }",
        "function int(num) { }",
        "function isSubscribe(key) { }",
        "function assert(state) { }",
    ]

    return function_lst


def save_js_functions(js_functions, output_path):
    out_lines = [it + "\n" for it in js_functions]
    with open(output_path, "a") as writer:
        writer.writelines(out_lines)


def convert_var_to_js_grammar(var_statement):
    """
    convert var statement from antlr to js grammar
    :param var_statement: var statement in antlr grammar,
    when parsing, it must full match "var(FIRST,SECOND);",
    otherwise, return the original statement
    :return: str, in js grammar, like "var FIRST = SECOND;"
    """
    statement = var_statement
    l_space_num = len(statement) - len(statement.lstrip())
    var_ptn = "var *\( *(\w+), *(.*)\) *;"
    if re.fullmatch(var_ptn, statement.strip()):
        first, second = re.findall(var_ptn, statement)[0]
        return "{}var {} = {};".format(" " * l_space_num, first, second)
    else:
        return var_statement


def revert_var_from_js_grammar(var_statement):
    """
    revert var statement from js to antlr grammar
    :param var_statement: var statement in js grammar,
    when parsing, it must full match "var FIRST = SECOND;",
    otherwise, return the original statement
    :return: str, in antlr grammar, like "var(FIRST,SECOND);"
    """
    statement = var_statement
    l_space_num = len(statement) - len(statement.lstrip())
    var_ptn = "var (.*) = (.*);"
    if re.fullmatch(var_ptn, statement.strip()):
        items = re.findall(var_ptn, statement.strip())[0]
        first, second = items

        return " " * l_space_num + "var({},{});".format(first, second)
    else:
        return var_statement


def convert_elif_to_js_grammar(line):
    return line.replace("elif", "else if")


def revert_elif_from_js_grammar(line):
    return line.replace("else if", "elif")


def convert_antlr_to_js(antlr, leading_space=" " * 4):
    if not antlr:
        return ""

    antlr_codes = antlr.split("\n")
    js_codes = []
    if len(antlr_codes) == 1:
        js_codes.append(antlr_codes[0])
    else:
        for line in antlr_codes:
            if line.lstrip().startswith("var("):
                js_codes.append(convert_var_to_js_grammar(line))
            elif "elif" in line:
                js_codes.append(convert_elif_to_js_grammar(line))
            else:
                js_codes.append(line)

    js_codes = "\n".join([leading_space + line for line in js_codes])

    return js_codes


def revert_antlr_from_js(js_codes):
    if not js_codes:
        return ""

    antlr_codes = []
    js_codes = js_codes.split("\n")
    if len(js_codes) == 1:
        return js_codes[0]
    else:
        for line in js_codes:
            if line.lstrip().startswith("var "):
                antlr_codes.append(revert_var_from_js_grammar(line))
            elif "else if" in line:
                antlr_codes.append(revert_elif_from_js_grammar(line))
            else:
                antlr_codes.append(line)

        return "\n".join(antlr_codes)


def convert_tpl_item_to_js_function(tpl_item):
    """
    convert tpl_item to js function
    :param tpl_item: input tpl item, in format {"intent": INTENT, "param": PARAM, "command": CMD, "antlr": TPL}
    :return: str, represent the corresponding js codes
for example:
input:
{'intent': 'charge_port_open',
 'param': None,
 'command': None,
 'antlr': "if(isSubscribe('charge.direct.port.on.status')){\n var(_status,data('charge.direct.port.on.status'));
 \n if(eqMethod(_status,1)){\n  cmd('charge.direct.port.on');\n  tts('充电口盖已打开');\n }\n elif(eqMethod(_status,2)){
 \n  tts('行车过程中,充电口盖暂不支持打开哦');\n }\n elif(eqMethod(_status,3)){\n  tts('当前充电口状态不支持打开或关闭哦');\n }
 \n}else{\n assert(isSubscribe('charge.direct.port.on'));\n if(data('charge.direct.port.on.support')){
 \n  cmd('charge.direct.port.on');\n  tts('充电口盖已打开');\n }else{
 \n  tts('行车过程中或充电枪插入或充电口盖打开时，充电口盖暂不支持打开哦');\n }\n}
}
output:
'function antlr(intent="charge_port_open", param="None", command="None") {
\n    if(isSubscribe(\'charge.direct.port.on.status\')){\n     var _status = data(\'charge.direct.port.on.status\');
\n     if(eqMethod(_status,1)){\n      cmd(\'charge.direct.port.on\');\n      tts(\'充电口盖已打开\');\n     }
\n     else if(eqMethod(_status,2)){\n      tts(\'行车过程中,充电口盖暂不支持打开哦\');\n     }
\n     else if(eqMethod(_status,3)){\n      tts(\'当前充电口状态不支持打开或关闭哦\');\n     }\n    }else{
\n     assert(isSubscribe(\'charge.direct.port.on\'));\n     if(data(\'charge.direct.port.on.support\')){
\n      cmd(\'charge.direct.port.on\');\n      tts(\'充电口盖已打开\');\n     }else{
\n      tts(\'行车过程中或充电枪插入或充电口盖打开时，充电口盖暂不支持打开哦\');\n     }\n    }\n}'
    """
    try:
        intent = tpl_item["intent"]
        param = tpl_item["param"]
        command = tpl_item["command"]
        antlr = tpl_item["antlr"]
        js_head = 'function antlr(intent="{}", param="{}", command="{}")'.format(intent or "None", param or "None",
                                                                                 command or "None") + " {"
        js_codes = convert_antlr_to_js(antlr=antlr)
        js_tail = "}"
        js_func = "\n".join([js_head, js_codes, js_tail])

        return js_func
    except KeyError:
        print(tpl_item)
        traceback.print_exc()

        return ""


def revert_tpl_item_from_js_function(js_func):
    js_func = js_func.strip().split("\n")

    js_head, js_codes, js_tail = js_func[0], "\n".join(js_func[1:-1]), js_func[-1]
    params = re.findall('\"(.*?)\"', js_head)
    tpl_item = {}
    for key, val in zip(["intent", "param", "command"], params):
        tpl_item[key] = None if val == "None" else val

    antlr = revert_antlr_from_js(js_codes)
    tpl_item["antlr"] = antlr

    return tpl_item


@time_cost
def save_json_list_to_js_file(json_lst, js_path, overwrite=True):
    if overwrite and os.path.exists(js_path):
        os.remove(js_path)
    save_js_functions(get_pre_defined_function(), output_path=js_path)

    js_functions = []
    for tpl_item in json_lst:
        js_func = convert_tpl_item_to_js_function(tpl_item=tpl_item)
        js_functions.append(js_func)

    save_js_functions(js_functions, output_path=js_path)
    return


@time_cost
def load_json_list_from_js_file(js_path):
    json_lst = []
    with open(js_path, "r") as reader:
        lines = "".join(reader.readlines())
        js_functions = re.split(pattern="function antlr", string=lines)[1:]  # ignore predefined functions
        for js_func in js_functions:
            tpl_item = revert_tpl_item_from_js_function(js_func)
            json_lst.append(tpl_item)

    return json_lst


@time_cost
def convert_js_to_xlsx(js_path, xlsx_path, sheet_name: str=None):
    if not sheet_name:
        assert os.path.isdir(js_path), "when sheet_name is not specified, js_path should be dir"
        f_names = os.listdir(js_path)
        for f_name in f_names:
            sheet_name = str(f_name.split("/")[-1]).split(".")[0]
            js_path_i = os.path.join(js_path, f_name)
            json_lst = load_json_list_from_js_file(js_path_i)
            save_json_list_into_xlsx(xlsx_path=xlsx_path, json_lst=json_lst, sheet_name=str(sheet_name))
    else:
        assert os.path.isfile(js_path), "when sheet_name is specified, js_path should be file"
        json_lst = load_json_list_from_js_file(js_path)
        save_json_list_into_xlsx(xlsx_path=xlsx_path, json_lst=json_lst, sheet_name=sheet_name)

    return


@time_cost
def revert_js_from_xlsx(js_path, xlsx_path, sheet_name=None):
    if not sheet_name:
        if os.path.exists(js_path):
            assert os.path.isdir(js_path), "when sheet_name is not specified, js_path should be dir"
        else:
            os.mkdir(js_path)
        json_dct = load_json_list_from_xlsx(xlsx_path=xlsx_path, sheet_name=sheet_name)
        for sheet_name, json_lst in json_dct.items():
            js_path_i = os.path.join(js_path, "{}.js".format(sheet_name))
            save_json_list_to_js_file(js_path=js_path_i, json_lst=json_lst)
    else:
        assert os.path.isfile(js_path), "when sheet_name is specified, js_path should be file"
        json_lst = load_json_list_from_xlsx(xlsx_path=xlsx_path, sheet_name=sheet_name)[sheet_name]
        save_json_list_to_js_file(js_path=js_path, json_lst=json_lst)

    return


def equal_codes(code1, code2, ignore_whitespace=True):
    """
    check two codes, if they are equal, return True; else, return False
    :param code1: the code to compare
    :param code2: the other code to compare
    :param ignore_whitespace: ignore whitespace or not, default True
    :return:
    """
    code1 = str(code1)
    code2 = str(code2)

    whitespace_ptn = "\r|\n|\t|\v| "
    if ignore_whitespace:
        code1 = re.sub(whitespace_ptn, "", code1)
        code2 = re.sub(whitespace_ptn, "", code2)

    return code1 == code2


@time_cost
def check_convert_result_between_antlr_and_js(original_tpl_xlsx_path, convert_tpl_xlsx_path, sheet_name=None):
    """
    check the convert result between antlr and js grammar
    :param original_tpl_xlsx_path: the original tpl file, in xlsx
    :param convert_tpl_xlsx_path: the convert tpl file, in xlsx
    :param sheet_name: the specified sheet, None indicates all sheets
    we first read tpl_item list from original_tpl_xlsx_path,
    then read antlr->js->antlr converted tpl_item list from convert_tpl_xlsx_path,
    then use equal_codes() to compare antlr codes in each tpl_item,
    and output result
    :return: dict, in format {SHEET_NAME1: [(INTENT1, BRANCH1), ...], ...}
    """
    original_tpl_items = load_json_list_from_xlsx(xlsx_path=original_tpl_xlsx_path, sheet_name=sheet_name)
    convert_tpl_items = load_json_list_from_xlsx(xlsx_path=convert_tpl_xlsx_path, sheet_name=sheet_name)
    diff_info = {}
    for sheet_name in original_tpl_items:
        diff_info[sheet_name] = []
        org_tpl_lst = original_tpl_items[sheet_name]
        cvt_tpl_lst = convert_tpl_items[sheet_name]
        for tpl_item1, tpl_item2 in zip(org_tpl_lst, cvt_tpl_lst):
            if None in tpl_item1:
                tpl_item1.pop(None)
            if None in tpl_item2:
                tpl_item2.pop(None)
            if not equal_codes(tpl_item1, tpl_item2):
                diff_info[sheet_name].append((tpl_item1["intent"], tpl_item1["param"]))

        if not diff_info[sheet_name]:
            diff_info.pop(sheet_name)

    print(format_string("convert between antlr and js result:"))
    for sheet_name in diff_info:
        print(format_string(sheet_name))
        print("bad convert num: {}".format(len(diff_info[sheet_name])))
        for i, pr in enumerate(diff_info[sheet_name]):
            print("{:03d}: intent: {}, branch: {}".format(i + 1, pr[0], pr[1]))

    return diff_info, original_tpl_items, convert_tpl_items
