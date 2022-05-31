# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# email : zhanzhiqiang09@126.com 
# date  : 2022/3/4
#
import collections
import re
import sys

from utils import *
sys.path.append("/Users/zhanzq/github")
from antlr4_python.data_utils import get_tree, format_tree

import traceback


class TPL(object):
    tts_map = dict()
    nlg_id_map = dict()
    tts_id_map = dict()

    def __init__(self, tpl_xlsx_path, do_not_parse_perceptual=True):
        self.tpl_data_path = tpl_xlsx_path
        self.tpl_dct = load_jsons_from_xlsx(xlsx_path=self.tpl_data_path)
        self.tts_dist = {}
        self.diff_tts_dist = {}
        self.tts_lst = []
        self.diff_tts_lst_per_tpl = []
        self.diff_tts_lst_all_tpl = []
        self.tpl_info_lst = []
        self.multi_intent_condition_mp = dict()
        self.data_lst = []
        self.bad_conds = set()

        slot_info_path = "/Users/zhanzq/Downloads/slot_info.json"
        slot_info_dct = load_from_json(slot_info_path)

        perceptual_data_dct = {}
        if not do_not_parse_perceptual:
            perceptual_data_path = "/Users/zhanzq/Downloads/感知点汇总.xlsx"
            perceptual_data_dct, perceptual_info_lst = parse_perceptual_data(perceptual_data_path)
            print("total perceptual data: {}".format(len(perceptual_data_dct)))
        self.analysis_all_tpl_items(slot_info_dct=slot_info_dct, perceptual_data_dct=perceptual_data_dct)
        self.print_parse_info()

    def analysis_tpl_data(self, version, car_type="E38"):
        all_tts_info = []
        for tpl_info in self.tpl_info_lst:
            for tts_info in tpl_info["tts_info_lst"]:
                try:
                    all_tts_info.append({
                        "domain": tpl_info["domain"],
                        "intent": tpl_info["intent"],
                        "slot": tpl_info["slot"],
                        "槽位语义": tpl_info["槽位语义"],
                        "tts": TPL.format_tts_with_idx(tts_info["tts"]),
                        "condition": tts_info["condition"],
                        "判断条件语义信息": tts_info["判断条件语义信息"],
                        "未成功解析的判断条件": tts_info["未成功解析的判断条件"],
                        "exact_condition_lst": tts_info["exact_condition_lst"],
                        "nlg_md5": tts_info["nlg_md5"],
                        "nlg_id": tts_info["nlg_id"],
                        "tpl": tpl_info["tpl"],
                        "formatted": True
                    })
                except Exception as e:
                    print(e)
                    traceback.print_exc()

        print("total tts num: {}".format(len(all_tts_info)))
        tts_info_path = "/Users/zhanzq/Downloads/tts_info.xlsx"
        save_jsons_into_xlsx(json_lst=all_tts_info, xlsx_path=tts_info_path,
                             sheet_name="{}_{}_md5".format(car_type, version))
        tts_info_jsonl_path = "/Users/zhanzq/Downloads/tts_info_md5_{}_{}.jsonl".format(car_type, version)
        save_to_jsonl(json_lst=all_tts_info, jsonl_path=tts_info_jsonl_path)

        return

    @staticmethod
    def format_tts_with_idx(tts):
        try:
            tts_lst = re.findall("[\"'](.*?)[\"']", tts)
            text_lst = []
            for i, text in enumerate(tts_lst):
                if "data" in text:
                    break
                else:
                    text_lst.append("{}. {}".format(i + 1, text.strip()))

            return "\n".join(text_lst)
        except:
            print(tts)
            traceback.print_exc()

            return tts

    @staticmethod
    def get_bad_tokens(tpl):
        if not tpl:
            return set()
        bad_token_ptn = "[^'\"](#.*?#)[^'\"]"
        lst = re.findall(bad_token_ptn, tpl)
        return set(lst)

    @staticmethod
    def get_good_tokens(tpl):
        if not tpl:
            return set()
        good_token_ptn = "['\"](#.*?#)['\"]"
        lst = re.findall(good_token_ptn, tpl)
        return set(lst)

    def get_all_bad_tokens(self):
        # get all bad and good tokens in "#.*#" format in tpl data
        bad_tokens = set()
        good_tokens = set()
        for car_type, tpl_items in self.tpl_dct.items():
            for item in tpl_items:
                tpl = item["antlr"]
                st = TPL.get_bad_tokens(tpl)
                bad_tokens = bad_tokens.union(st)
                good_tokens = good_tokens.union(TPL.get_good_tokens(tpl))
        print("bad tokens: {}".format(bad_tokens))
        print("good tokens: {}".format(good_tokens))

        return bad_tokens

    def update_perceptual_data_st(self, tpl_item):
        data = tpl_item.data
        self.data_lst.extend(data)

    @staticmethod
    def get_slot_info(slot, slot_info_dct):
        slot_info = None
        if slot_info_dct:
            slot_info = slot_info_dct.get(slot, {}).get("semantics")

        return slot_info

    def update_parse_info(self, tpl_item):
        tts_lst = tpl_item.tts_lst

        tts_num = len(tpl_item.tts_lst)
        self.tts_dist[tts_num] = self.tts_dist.get(tts_num, 0) + 1
        self.tts_lst.extend(tts_lst)
        diff_tts_lst = list(set(tts_lst))
        diff_tts_num = len(diff_tts_lst)
        self.diff_tts_dist[diff_tts_num] = self.diff_tts_dist.get(diff_tts_num, 0) + 1
        self.diff_tts_lst_per_tpl.extend(diff_tts_lst)
        self.diff_tts_lst_all_tpl.extend(tts_lst)
        tpl_info = {
            "domain": tpl_item.domain,
            "intent": tpl_item.intent,
            "slot": tpl_item.slot,
            "tts_info_lst": tpl_item.tts_info_lst,
            "tpl": tpl_item.tpl,
        }
        self.tpl_info_lst.append(tpl_info)

    @staticmethod
    def get_condition_semantic(exact_cond_lst, cond_semantic_dct):
        semantics, bad_cond_st = convert_condition_to_semantics(cond_lst=exact_cond_lst, cond_dct=cond_semantic_dct)

        return semantics, bad_cond_st

    def update_cond_semantics(self, tpl_item, cond_semantic_dct):
        for tts_info in tpl_item.tts_info_lst:
            exact_cond_lst = tts_info["exact_condition_lst"]
            semantics, bad_cond_st = TPL.get_condition_semantic(exact_cond_lst=exact_cond_lst,
                                                                cond_semantic_dct=cond_semantic_dct)
            tts_info["判断条件语义信息"] = semantics
            failed_cond_lst = list(bad_cond_st) if bad_cond_st else None
            tts_info["未成功解析的判断条件"] = failed_cond_lst
            self.bad_conds = self.bad_conds.union(bad_cond_st)

        return

    def print_parse_info(self):
        tts_dist = list(self.tts_dist.items())
        tts_dist.sort()
        diff_tts_dist = list(self.diff_tts_dist.items())
        diff_tts_dist.sort()

        # print("domain: {}".format(domain))
        print("tts_dist: {}".format(tts_dist))
        print("diff_tts_dist: {}".format(diff_tts_dist))
        print("TTS总数量: {}".format(len(self.tts_lst)))
        print("按单个tpl去重后TTS数量: {}".format(len(self.diff_tts_lst_per_tpl)))
        print("按所有tpl去重后TTS数量: {}".format(len(self.diff_tts_lst_all_tpl)))
        print("\n\n")

    def analysis_all_tpl_items(self, domain=None, car_type="E38", slot_info_dct=None, perceptual_data_dct=None):
        tpl_items = self.tpl_dct[car_type]
        for item in tpl_items:
            tpl_item = TplItem(item, self.tts_map, self.nlg_id_map, self.tts_id_map)
            print("intent: {}, slot: {}".format(tpl_item.intent, tpl_item.slot))
            if domain is not None and domain != tpl_item.domain:
                continue
            self.update_cond_semantics(tpl_item=tpl_item, cond_semantic_dct=perceptual_data_dct)
            self.update_parse_info(tpl_item)
            self.tpl_info_lst[-1]["槽位语义"] = TPL.get_slot_info(slot=tpl_item.slot, slot_info_dct=slot_info_dct)

            self.tts_map = tpl_item.tts_map
            self.tts_id_map = tpl_item.tts_id_map
            self.nlg_id_map = tpl_item.nlg_id_map

        self.diff_tts_lst_all_tpl = list(set(self.diff_tts_lst_all_tpl))


class TplItem(object):
    def __init__(self, tpl_item, tts_map={}, nlg_id_map={}, tts_id_map={}):
        self.intent = tpl_item.get("intent") or ""
        self.slot = tpl_item.get("slot", tpl_item.get("param")) or "default"
        self.tpl = tpl_item.get("antlr") or ""
        if "_" in self.intent:
            self.domain = self.intent.split("_")[0]
        else:
            self.domain = self.intent

        self.tts_map = tts_map
        self.nlg_id_map = nlg_id_map
        self.tts_id_map = tts_id_map
        self.tts_lst = []
        self.tts_info_lst = []
        self.conditions = {}
        self.data = {}

        self.parse_tpl_item()

    def __str__(self):
        ret_obj = {
            "intent": self.intent,
            "slot": self.slot,
            "tpl": self.tpl,
            "data": self.data,
            "conditions": self.conditions
        }

        return json.dumps(ret_obj, ensure_ascii=False, indent=4)

    @staticmethod
    def get_param_dct(format_codes):
        param_dct = {}
        if not format_codes:
            return param_dct
        for line in format_codes.split("\n"):
            TplItem.update_param_dct(param_dct=param_dct, line=line)

        return param_dct

    @staticmethod
    def update_param_dct(param_dct, line):
        """
        update param dict, according to the input code line
        :param param_dct: param dict, format as {"_status", "data('ac.inner.temp')"}
        :param line:
        :return:
        """
        var_ptn = "var *\((.*?), *(.*)\)"
        if line.strip().startswith("var"):
            pr = re.findall(var_ptn, line)[0]
            param_dct[pr[0]] = TplItem.convert_cond_to_exact_info(cond=pr[1], param_dct=param_dct)

        return

    @staticmethod
    def convert_cond_to_exact_info(cond, param_dct):
        """
        convert condition to exact info, like "eqMethod(_status, 1)" ==> eqMethod(data('ac.inner.temp'), 1)"
        :param cond:
        :param param_dct:
        :return:
        """
        if not cond:
            return cond

        # cond_lst = re.findall("[\(, ](_\w+)", cond)
        cond_lst = re.findall("\w*_\w+", cond)
        if cond_lst:
            cond_lst = [cond for cond in cond_lst if cond.startswith("_")]
        if cond in param_dct:
            cond_lst.append(cond)
        cond_lst.sort(key=lambda it: -len(it))
        for cond_i in cond_lst:
            if cond_i in param_dct:
                new_cond = cond.replace(cond_i, param_dct[cond_i])
                # print("convert {} to {}".format(cond, new_cond))
                cond = new_cond

        cond = TplItem.process_specific_condition(cond)

        return cond

    @staticmethod
    def is_full(s):
        val = 0
        for ch in s:
            if ch == '(':
                val += 1
            elif ch == ')':
                val -= 1

        return val == 0

    @staticmethod
    def process_int_condition(cond):
        ptn = "int\(.*?\)"
        lst = re.findall(ptn, cond)
        if lst:
            for item in lst:
                new_item = item[4:]
                if not TplItem.is_full(new_item):
                    new_item = new_item[:-1]
                # print("convert {} to {}".format(item, new_item))
                cond = cond.replace(item, new_item)

        return cond

    @staticmethod
    def process_data_condition(cond):
        ptn = "data\(data\(.*?\)\)"
        lst = re.findall(ptn, cond)
        if lst:
            for item in lst:
                # print("convert {} to {}".format(item, item[5:-1]))
                cond = cond.replace(item, item[5:-1])

        return cond

    @staticmethod
    def process_subscribe_condition(cond):
        ptn = "isSubscribe\(data\(.*?\)\)"
        lst = re.findall(ptn, cond)
        if lst:
            for item in lst:
                new_item = item[:12] + item[17:-1]
                # print("convert {} to {}".format(item, new_item))
                cond = cond.replace(item, new_item)

        return cond

    @staticmethod
    def process_specific_condition(cond):
        cond = TplItem.process_int_condition(cond)
        cond = TplItem.process_data_condition(cond)
        cond = TplItem.process_subscribe_condition(cond)

        return cond

    def parse_tpl_item(self):
        """
        parse single tpl record
        """
        try:
            self.tpl = format_tree(get_tree(self.tpl), -1)
            # self.data = self.get_perception_data()
            # self.conditions = self.get_conditions()
            self.insert_nlg_md5_v2()
            if len(self.tts_lst) == 0:
                print(self)
        except Exception as e:
            print("intent: {}".format(self.intent))
            print(traceback.print_exc())

        return

    def get_perception_data(self,):
        """
        get all perceptual data
        :return:
        """
        data_lst = []
        data_ptn = "data\([^()]*?([_a-zA-Z.]+.[_a-zA-Z.]+.[_a-zA-Z.]+)[^()]*?\)"
        code_lines = self.tpl.split("\n")
        for line in code_lines:
            data_lst.extend(re.findall(data_ptn, line))

        return dict(collections.Counter(data_lst).most_common())

    def get_conditions(self,):
        conditions = []
        if_ptn = "if *\((.*)\)"
        elif_ptn = "elif *\((.*)\)"
        cond_ptn = "([a-zA-Z]+ ?\([^()]+\))"
        code_lines = self.tpl.split("\n")
        for line in code_lines:
            line = line.strip()
            cond = ""
            if line.startswith("if"):
                cond = re.findall(if_ptn, line)[0]
            elif line.startswith("}elif"):
                cond = re.findall(elif_ptn, line)[0]

            if cond:
                conditions.extend(re.findall(cond_ptn, cond))

        return dict(collections.Counter(conditions).most_common())

    def get_tts_info_v2(self, tts, condition):
        nlg_md5 = gen_id(self.intent + self.slot + condition, len_id=32)

        tts_info = {
            "tts": tts,
            "nlg_md5": nlg_md5,
            "condition": condition,
            "params": TplItem.get_params(tts)
        }

        return tts_info

    def insert_nlg_md5_v2(self):
        add_tpl_lines = []
        condition_stk = []
        param_dct = {}
        code_lines = self.tpl.split("\n")
        for i, line in enumerate(code_lines):
            update_condition(line, condition_stk)
            TplItem.update_param_dct(param_dct, line)
            if line.lstrip().startswith("tts("):
                tts_level = get_indent_level(line)
                while len(condition_stk) > tts_level:
                    condition_stk.pop()

                leading_spaces = " " * (len(line) - len(line.lstrip()))
                condition_lst = [item[-1][1] for item in condition_stk]
                condition = " and ".join(condition_lst)
                if condition:
                    exact_condition_lst = [TplItem.convert_cond_to_exact_info(cond, param_dct) for cond in condition.split(" and ")]
                else:
                    exact_condition_lst = []
                tts = line.strip()
                tts_info = self.get_tts_info_v2(tts, condition)
                tts_info["exact_condition_lst"] = exact_condition_lst
                self.tts_lst.append(tts)
                add_tpl_lines.append(line)
                nxt_line = None
                if i < len(code_lines) - 1:
                    nxt_line = code_lines[i+1].strip()
                if not nxt_line or not nxt_line.startswith("nlg("):
                    add_tpl_lines.append('{}nlg("{}");'.format(leading_spaces, tts_info["nlg_md5"]))
                    tts_info["nlg_id"] = None
                else:
                    tts_info["nlg_id"] = re.findall("nlg\([\"'](.*)[\"']\)", nxt_line)[0]
                self.tts_info_lst.append(tts_info)
            else:
                add_tpl_lines.append(line)

        self.tpl = "\n".join(add_tpl_lines)
        return

    def add_param_into_nlg(self):
        code_lines = self.tpl.split("\n")
        out_lines = code_lines[:]
        for i, line in enumerate(code_lines):
            if line.lstrip().startswith("tts("):
                if "%s" in line:
                    params = TplItem.get_params(line)
                    param = None
                    if not params:
                        print("intent: {}, line: {:3d}, bad tts format: {}".format(self.intent, i+1, line))
                        continue
                    else:
                        for idx, param_i in enumerate(params):
                            if "data(" in param_i:
                                perceptual_name = re.findall("\w+\.[\w\.]+", param_i)[0]
                                perceptual_name = "_" + perceptual_name.replace(".", "_")
                                leading_whitespace_num = len(line) - len(line.lstrip())
                                add_line = "var({},{});".format(perceptual_name, param_i)
                                out_lines[i] += "\n" + " " * leading_whitespace_num + add_line
                                params[idx] = perceptual_name

                        if len(params) == 1:
                            param = "{'nlg_target': '%s'}" % params[0]
                        elif len(params) == 2:
                            print("two params: {}".format(line))
                            param = "{'nlg_source': '%s', 'nlg_target': '%s'}" % (params[0], params[1])
                        else:
                            print("intent: {}, line: {:3d}, bad tts format: {}".format(self.intent, i+1, line))

                        for param_i in params:
                            if "data(" in param_i:
                                print("intent: {}, line: {:3d}, bad tts format: {}".format(self.intent, i+1, line))

                        if i+1 >= len(out_lines):
                            print("not insert nlg() in {}".format(self.intent))
                            continue

                        if param in out_lines[i+1]:
                            continue
                        else:
                            out_lines[i+1] = out_lines[i+1].replace(");", ', "{}");'.format(param))

        self.tpl = "\n".join(out_lines)
        return

    @staticmethod
    def get_params(tts):
        """
        get parameters in tts
        :param tts: input tts, format like "tts('温度给你调低了', '温度已调低', _tempResult);"
        :return:
        """
        param_ptn = "_[^(){},; ]*|data\([^()]*?\)"
        params = re.findall(param_ptn, tts)

        return params


def process_slot_info():
    slot_info_path = "/Users/zhanzq/Downloads/slot_info.xlsx"

    sheet_name = "产品待确认的槽位语义信息_0331"
    slot_info_lst = load_jsons_from_xlsx_v2(xlsx_path=slot_info_path, sheet_name=sheet_name)[sheet_name]

    slot_info_dct = {}
    for slot_info in slot_info_lst:
        domain = slot_info["domain"]
        slot = slot_info["slot"]
        val = slot_info["val"]
        prefer = slot_info["Prefer"]
        key = "{}={}".format(slot, val)
        slot_info_dct[key] = {
            "domain": domain,
            "semantics": prefer,
        }

    save_to_json(json_obj=slot_info_dct, json_path="/Users/zhanzq/Downloads/slot_info.json")

    return


def split_expr(s):
    s += ","
    #     print("input: ", s)
    val = 0
    res = []
    pre = 0
    for i, ch in enumerate(s):
        if s[i] == '(':
            val += 1
        elif s[i] == ')':
            val -= 1
        elif s[i] == ',' and val == 0:
            res.append(s[pre:i])
            pre = i
            if s[i] == ',':
                pre += 1
    #     print("output: ", res)

    return res


def parse_or(s):
    if not s.startswith("or"):
        return split_expr(s)
    else:
        s = s[3:-1]
    res = []
    s_lst = split_expr(s)
    for s_i in s_lst:
        res.extend(parse_or(s_i))

    return res


def parse_and(s):
    if not s.startswith("and"):
        return split_expr(s)
    else:
        s = s[4:-1]
    res = []
    s_lst = split_expr(s)
    for s_i in s_lst:
        res.extend(parse_and(s_i))

    return res


def format_cond(cond):
    if cond.startswith("not "):
        cond = cond[4:]
    if cond.startswith("!"):
        cond = cond[1:]
    if cond.startswith("and("):
        return parse_and(cond)
    elif cond.startswith("or("):
        return parse_or(cond)
    else:
        return [cond]


def convert_or_cond_to_semantics(cond_lst, cond_dct):
    res = []
    bad_conds = set()
    for i, cond in enumerate(cond_lst):
        if cond not in cond_dct:
#             print("condition {} not found".format(cond))
            bad_conds.add(cond)
        else:
            res.append("{}".format(cond_dct[cond]))

    return "  或\n  ".join(res), bad_conds


def convert_and_cond_to_semantics(cond_lst, cond_dct):
    res = []
    bad_conds = set()
    for i, cond in enumerate(cond_lst):
        if cond not in cond_dct:
#             print("condition {} not found".format(cond))
            bad_conds.add(cond)
        else:
            res.append("{}".format(cond_dct[cond]))

    return "  且\n  ".join(res), bad_conds


def convert_notor_cond_to_semantics(cond_lst, cond_dct):
    res = []
    bad_conds = set()
    for i, cond in enumerate(cond_lst):
        cond = "not " + cond
        if cond not in cond_dct:
#             print("condition {} not found".format(cond))
            bad_conds.add(cond)
        else:
            res.append("{}".format(cond_dct[cond]))

    return "  且\n  ".join(res), bad_conds


def convert_notand_cond_to_semantics(cond_lst, cond_dct):
    res = []
    bad_conds = set()
    for i, cond in enumerate(cond_lst):
        cond = "not " + cond
        if cond not in cond_dct:
#             print("condition {} not found".format(cond))
            bad_conds.add(cond)
        else:
            res.append("{}".format(cond_dct[cond]))

    return "  或\n  ".join(res), bad_conds


def convert_condition_to_semantics(cond_lst, cond_dct):
    res = []
    bad_conds = set()
    for i, cond in enumerate(cond_lst):
        if cond.startswith("not "):
            cond = cond[:4] + cond[4:].replace(" ", "")
        else:
            cond = cond.replace(" ", "")
        cond = cond.replace("\"", "'")
        cond = cond.replace("\\'", "'")
        if cond.startswith("or("):
            tmp_lst = parse_or(cond)
            tmp_res, tmp_bad_conds = convert_or_cond_to_semantics(tmp_lst, cond_dct)
            bad_conds = bad_conds.union(tmp_bad_conds)
            res.append("{}. {}".format(i+1, tmp_res))
        elif cond.startswith("and("):
            tmp_lst = parse_and(cond)
            tmp_res, tmp_bad_conds = convert_and_cond_to_semantics(tmp_lst, cond_dct)
            bad_conds = bad_conds.union(tmp_bad_conds)
            res.append("{}. {}".format(i+1, tmp_res))
        elif cond.startswith("not or("):
            cond = cond[4:]
            tmp_lst = parse_or(cond)
            tmp_res, tmp_bad_conds = convert_notor_cond_to_semantics(tmp_lst, cond_dct)
            bad_conds = bad_conds.union(tmp_bad_conds)
            res.append("{}. {}".format(i+1, tmp_res))
        elif cond.startswith("not and("):
            cond = cond[4:]
            tmp_lst = parse_and(cond)
            tmp_res, tmp_bad_conds = convert_notand_cond_to_semantics(tmp_lst, cond_dct)
            bad_conds = bad_conds.union(tmp_bad_conds)
            res.append("{}. {}".format(i+1, tmp_res))
        elif cond not in cond_dct:
            # print("condition {} not found".format(cond))
            bad_conds.add(cond)
        else:
            res.append("{}. {}".format(i+1, cond_dct[cond]))

    return "\n".join(res), bad_conds


def parse_perceptual_ret_vals(ret_vals, data_item=None):
    if not ret_vals:
        return {}
    else:
        res = {}
        for item in ret_vals.split(";"):
            item = item.strip()
            if item:
                try:
                    key, val = item.split(":")
                    res[key] = val
                except:
                    print("data: {}, bad format: \n{}".format(data_item["感知点"], item))

        return res


def parse_input_param(param):
    param_lst = param.split(";")
    param_dct = {}
    for param_i in param_lst:
        if not param_i:
            continue
        key, val = param_i.split(":")
        key = key.strip()
        val = val.strip()
        param_dct[key] = {}
        val_lst = val.strip()[1:-1].split(",")
        for val_i in val_lst:
            _key, _val = val_i.split("=")
            _key = _key.strip()
            _val = _val.strip()
            param_dct[key][_key] = _val

    return param_dct


def get_subscribe_method(item):
    name = item["感知点"] or ""
    entity = item["实体"] or ""
    prop = item["属性"] or ""
    action = item["动作"] or ""
    ret_vals = item["返回值域"] or ""
    unit = item["单位"] or ""
    param = item["接口调用参数"] or ""

    res = {
        "isSubscribe('{}')".format(name): "'{}感知点' 已注册".format(name),
        "not !isSubscribe('{}')".format(name): "'{}感知点' 已注册".format(name),
        "not isSubscribe('{}')".format(name): "'{}感知点' 未注册".format(name),
        "!isSubscribe('{}')".format(name): "'{}感知点' 未注册".format(name)
    }

    return res


def _cmp_method(key_s, val_s):
    tmp_s = key_s
    return {
        "eqMethod{}".format(tmp_s): val_s.format("等于"),
        "not neqMethod{}".format(tmp_s): val_s.format("等于"),
        "!neqMethod{}".format(tmp_s): val_s.format("等于"),
        "neqMethod{}".format(tmp_s): val_s.format("不等于"),
        "!eqMethod{}".format(tmp_s): val_s.format("不等于"),
        "not eqMethod{}".format(tmp_s): val_s.format("不等于"),

        "gtMethod{}".format(tmp_s): val_s.format("大于"),
        "not leMethod{}".format(tmp_s): val_s.format("大于"),
        "!leMethod{}".format(tmp_s): val_s.format("大于"),
        "geMethod{}".format(tmp_s): val_s.format("大于等于"),
        "not ltMethod{}".format(tmp_s): val_s.format("大于等于"),
        "!ltMethod{}".format(tmp_s): val_s.format("大于等于"),

        "ltMethod{}".format(tmp_s): val_s.format("小于"),
        "not geMethod{}".format(tmp_s): val_s.format("小于"),
        "!geMethod{}".format(tmp_s): val_s.format("小于"),
        "leMethod{}".format(tmp_s): val_s.format("小于等于"),
        "not gtMethod{}".format(tmp_s): val_s.format("小于等于"),
        "!gtMethod{}".format(tmp_s): val_s.format("小于等于"),
    }


def get_cmp_method(item):
    name = item["感知点"] or ""
    entity = item["实体"] or ""
    prop = item["属性"] or ""
    action = item["动作"] or ""
    ret_vals = item["返回值域"] or ""
    unit = item["单位"] or ""
    param = item["接口调用参数"] or ""

    ret_dct = parse_perceptual_ret_vals(ret_vals, item)

    res = {}
    # rule1: entity + prop + action + ret_dct[key]
    for key, val in ret_dct.items():
        #         try:
        #             val = eval(str(val))
        #         except:
        #             traceback.print_exc()
        #         if type(val) is not int and type(val) is not float:
        #             continue
        #         else:
        val_s = entity + prop + "{}" + str(val) + unit
        key_s = "(data('{}'),'{}')".format(name, key)
        res.update(_cmp_method(key_s, val_s))

        key_s = "(data('{}'),{})".format(name, key)
        res.update(_cmp_method(key_s, val_s))

    return res


def get_bool_method(item):
    name = item["感知点"] or ""
    entity = item["实体"] or ""
    prop = item["属性"] or ""
    action = item["动作"] or ""
    ret_vals = item["返回值域"] or ""
    unit = item["单位"] or ""
    param = item["接口调用参数"] or ""

    ret_dct = parse_perceptual_ret_vals(ret_vals, item)

    res = {}

    # rule1: entity + prop + action + ret_dct[key]
    for key, val in ret_dct.items():
        _val = entity + prop + action + str(val) + unit
        if key == "true":
            res["data('{}')".format(name)] = _val
            res["not !data('{}')".format(name)] = _val
        elif key == "false":
            res["!data('{}')".format(name)] = _val
            res["not data('{}')".format(name)] = _val

    return res


def get_single_param_method(item, param):
    name = item["感知点"] or ""
    entity = item["实体"] or ""
    prop = item["属性"] or ""
    action = item["动作"] or ""
    ret_vals = item["返回值域"] or ""
    unit = item["单位"] or ""
    #     param = item["接口调用参数"] or ""

    #     param = parse_input_param(param)
    ret_dct = parse_perceptual_ret_vals(ret_vals, item)

    res = {}
    # rule1: entity + prop + action + ret_dct[key]
    for key, val in ret_dct.items():
        slot = list(param.keys())[0].strip()
        param_dct = param[slot]
        for p, v in param_dct.items():
            val_s = v + entity + prop + "{}" + val + unit
            key_s = "(data('%s','{'%s':'%s'}'),%s)" % (name, slot, p, key)
            res.update(_cmp_method(key_s, val_s))

            key_s = "(data('%s','{'%s':%s}'),%s)" % (name, slot, str(p), key)
            res.update(_cmp_method(key_s, val_s))

            key_s = "(data('%s','{'%s':'%s'}'),'%s')" % (name, slot, p, key)
            res.update(_cmp_method(key_s, val_s))

            key_s = "(data('%s','{'%s':%s}'),'%s')" % (name, slot, str(p), key)
            res.update(_cmp_method(key_s, val_s))

    res.update(get_cmp_method(item))

    return res


def get_two_param_method(item, param):
    name = item["感知点"] or ""
    entity = item["实体"] or ""
    prop = item["属性"] or ""
    action = item["动作"] or ""
    ret_vals = item["返回值域"] or ""
    unit = item["单位"] or ""
    #     param = item["接口调用参数"] or ""

    #     param = parse_input_param(param)
    ret_dct = parse_perceptual_ret_vals(ret_vals, item)

    res = {}
    # rule1: entity + prop + action + ret_dct[key]
    for key, val in ret_dct.items():
        slot, slot2 = list(param.keys())
        param_dct1 = param[slot]
        param_dct2 = param[slot2]
        for p, v in param_dct1.items():
            for p2, v2 in param_dct2.items():
                val_s = v + v2 + entity + prop + "{}" + val + unit
                key_s = "(data('%s','{'%s':'%s','%s':'%s'}'),%s)" % (name, slot, p, slot2, p2, key)
                res.update(_cmp_method(key_s, val_s))

                key_s = "(data('%s','{'%s':'%s','%s':%s}'),%s)" % (name, slot, p, slot2, str(p2), key)
                res.update(_cmp_method(key_s, val_s))

                key_s = "(data('%s','{'%s':%s,'%s':'%s'}'),%s)" % (name, slot, str(p), slot2, p2, key)
                res.update(_cmp_method(key_s, val_s))

                key_s = "(data('%s','{'%s':%s,'%s':%s}'),%s)" % (name, slot, str(p), slot2, str(p2), key)
                res.update(_cmp_method(key_s, val_s))

                key_s = "(data('%s','{'%s':'%s','%s':'%s'}'),'%s')" % (name, slot, p, slot2, p2, key)
                res.update(_cmp_method(key_s, val_s))

                key_s = "(data('%s','{'%s':'%s','%s':%s}'),'%s')" % (name, slot, p, slot2, str(p2), key)
                res.update(_cmp_method(key_s, val_s))

                key_s = "(data('%s','{'%s':%s,'%s':'%s'}'),'%s')" % (name, slot, str(p), slot2, p2, key)
                res.update(_cmp_method(key_s, val_s))

                key_s = "(data('%s','{'%s':%s,'%s':%s}'),'%s')" % (name, slot, str(p), slot2, str(p2), key)
                res.update(_cmp_method(key_s, val_s))

    keys = list(param.keys())
    param1 = {keys[0]: param[keys[0]]}
    res.update(get_single_param_method(item, param1))

    param2 = {keys[1]: param[keys[1]]}
    res.update(get_single_param_method(item, param2))

    return res


def parse_perceptual_item_by_rules(item):
    res = get_subscribe_method(item)
    param = item["接口调用参数"] or ""
    try:
        res.update(get_cmp_method(item))
        res.update(get_bool_method(item))
    except Exception as e:
        traceback.print_exc()
    if param:
        try:
            param = parse_input_param(param)
            if len(param) == 1:
                res.update(get_single_param_method(item, param))
            elif len(param) == 2:
                res.update(get_two_param_method(item, param))
        except Exception as e:
            print(item)
            traceback.print_exc()

    return res


def get_from_manual_create():
    manual_cond_path = "/Users/zhanzq/Downloads/manual_cond.json"
    tmp_json = load_from_json(manual_cond_path)
    cond_dct = {}
    for key in tmp_json:
        pos_semantics = tmp_json[key]["condition_explain"]
        neg_semantics = tmp_json[key]["not_condition_explain"]

        cond_dct.update({
            key: pos_semantics,
            "not !" + key: pos_semantics,
            "not " + key: neg_semantics,
            "!" + key: neg_semantics
        })

    return cond_dct


def get_from_predefine_slot_info():
    slot_info_path = "/Users/zhanzq/Downloads/slot_info.json"
    slot_info_dct = load_from_json(slot_info_path)
    res = {}
    for key, item in slot_info_dct.items():
        slot, val = key.split("=")
        val_s = "{}" + (item["semantics"] or "UNK")
        key_s = "(#{}#,{})".format(slot, val)
        res.update(_cmp_method(key_s, val_s))

        key_s = "('#{}#',{})".format(slot, val)
        res.update(_cmp_method(key_s, val_s))

    pr_lst = [
        ["(#sound_location#,1)", "声源{}主驾"],
        ["(#sound_location#,2)", "声源{}副驾"],
        ["(#sound_location#,3)", "声源{}左后"],
        ["(#sound_location#,4)", "声源{}右后"],
        ["(#speech_version#,280)", "语音版本{}280"],
        ["('#placeholder_door_type#','鹏翼门')", "车门类型{}鹏翼门"],
        ["('#fullSceneSwitch#','true')", "全场景语音{}已打开"],
        ["(#整数#,0)", "query中的整数值{}0"],
        ["(#整数#,1)", "query中的整数值{}1"],
        ["(#整数#,3)", "query中的整数值{}3"],
        ["(#整数#,5)", "query中的整数值{}5"],
        ["(#整数#,20)", "query中的整数值{}20"],
        ["(#整数#,100)", "query中的整数值{}100"],
        ["(#槽整数#,0)", "query中的整数值{}0"],
        ["(#槽整数#,100)", "query中的整数值{}100"],
        ["(#整数#,data('ac.get.temp.max'))", "query中的整数值{}空调温度最大值"],
        ["(#整数#,data('ac.get.temp.min'))", "query中的整数值{}空调温度最小值"],
        ["(#整数#,data('ac.get.wind.max'))", "query中的整数值{}风量最大值"],
        ["(#整数#,data('ac.get.wind.min'))", "query中的整数值{}风量最小值"],
        ["(#整数#,data('ac.wind.speed.lv'))", "query中的整数值{}空调风速"],
        ["(#整数#,data('charge.discharge.limit.max.val'))", "query中的整数值{}充电限值的最大值"],
        ["(#整数#,data('charge.discharge.limit.min.val'))", "query中的整数值{}放电限值的最小值"],
        ["(#整数#,data('ac.driver.temp'))", "query中的整数值{}主驾空调温度"],
        ["(#整数#,data('ac.driver.psn'))", "query中的整数值{}主驾空调温度"],
        ["(#整数#,data('ac.driver.temp'))", "query中的整数值{}主驾空调温度"],
        ["(data('ac.wind.speed.lv'),14)", "空调风速{}14"],
    ]

    for key_s, val_s in pr_lst:
        res.update(_cmp_method(key_s, val_s))

    return res


def get_from_placeholder_info():
    pr_lst = [
        ["('#more#','true')", "query中{} '更|再' 或 '一些'"],
        ["('#增加一些#','true')", "query中{} '更|再' 或 '一些'"],
    ]

    res = {}
    for key_s, val_s in pr_lst:
        res.update(_bool_method(key_s, val_s))

    return res


def _bool_method(key_s, val_s):
    return {
        "eqMethod{}".format(key_s): val_s.format("含有"),
        "not neqMethod{}".format(key_s): val_s.format("含有"),
        "!neqMethod{}".format(key_s): val_s.format("含有"),
        "neqMethod{}".format(key_s): val_s.format("不含有"),
        "!eqMethod{}".format(key_s): val_s.format("不含有"),
        "not eqMethod{}".format(key_s): val_s.format("不含有"),
    }


def get_from_unity(unity_info_path=None):
    if not unity_info_path:
        unity_info_path = "/Users/zhanzq/Downloads/unity.xlsx"

    json_lst = load_jsons_from_xlsx_v2(xlsx_path=unity_info_path, sheet_name="Sheet1")["Sheet1"]
    res = {}
    for item in json_lst:
        key, val = item["未成功解析的判断条件"], item["语义"]
        if val:
            res[key] = val

    return res


def get_from_adjust_info(perceptual_data_path=None):
    if not perceptual_data_path:
        perceptual_data_path = "/Users/zhanzq/Downloads/感知点汇总.xlsx"
    sheet_name = "感知点汇总表"
    perceptual_data_lst = load_jsons_from_xlsx_v2(xlsx_path=perceptual_data_path, sheet_name=sheet_name)[sheet_name]
    res = {}
    for item1 in perceptual_data_lst:
        key1 = item1["感知点"]
        name1 = item1["name"]
        for item2 in perceptual_data_lst:
            key2 = item2["感知点"]
            name2 = item2["name"]
            pr_lst = [
                ["(data('{}')-#整数#,data('{}'))".format(key1, key2), "%s 调整后的值{} %s" % (name1, name2)],
                ["((data('{}')-#整数#),data('{}'))".format(key1, key2), "%s 调整后的值{} %s" % (name1, name2)],
                ["((data('{}')-#整数#-0.#小数#),data('{}'))".format(key1, key2), "%s 调整后的值{} %s" % (name1, name2)],
                ["(data('{}')+#整数#,data('{}'))".format(key1, key2), "%s 调整后的值{} %s" % (name1, name2)],
                ["((data('{}')+#整数#),data('{}'))".format(key1, key2), "%s 调整后的值{} %s" % (name1, name2)],
                ["((data('{}')+#整数#+0.#小数#),data('{}'))".format(key1, key2), "%s 调整后的值{} %s" % (name1, name2)],
            ]
            for key_s, val_s in pr_lst:
                res.update(_cmp_method(key_s, val_s))

    pr_lst = [
        ["(data('system.volume.current','{'stream_type':#stream_type#}')+#整数#,data('system.volume.max.value','{'stream_type':#stream_type#}'))", "当前音量调整后的值{}最大音量"],
        ["(data('system.volume.current','{'stream_type':#stream_type#}')-#整数#,data('system.volume.max.value','{'stream_type':#stream_type#}'))", "当前音量调整后的值{}最大音量"],
        ["(data('system.volume.current','{'stream_type':#stream_type#}')+#整数#,data('system.volume.min.value','{'stream_type':#stream_type#}'))", "当前音量调整后的值{}最小音量"],
        ["(data('system.volume.current','{'stream_type':#stream_type#}')-#整数#,data('system.volume.min.value','{'stream_type':#stream_type#}'))", "当前音量调整后的值{}最小音量"],
        ["(data('ac.psn.seat.blow.lv')+1),data('ac.get.seat.blow.max')", "副驾座椅通风档位调整后的值{}座椅通风最大值"],
        ["(data('ac.psn.seat.blow.lv')+1),data('ac.get.seat.blow.max')", "副驾座椅通风档位调整后的值{}座椅通风最大值"],
        ["(data('ac.psn.seat.blow.lv')+1),data('ac.get.seat.blow.max')", "副驾座椅通风档位调整后的值{}座椅通风最大值"],
        ["(data('ac.wind.speed.lv')+#整数#),data('ac.get.wind.max'))", "调整后的风速{}最大风速"],
        ["(data('ac.wind.speed.lv')+#整数#),data('ac.get.wind.max'))", "调整后的风速{}最大风速"],
        ["(data('ac.wind.speed.lv')-#整数#),data('ac.get.wind.min'))", "调整后的风速{}最小风速"],
        ["(data('system.icm.brightness.current')+#整数#,100)", "仪表盘亮度调整后的值{}最大亮度"],
        ["(data('system.icm.brightness.current')+#整数#,0)", "仪表盘亮度调整后的值{}最小亮度"],
    ]
    for key_s, val_s in pr_lst:
        res.update(_cmp_method(key_s, val_s))

    return res


def parse_perceptual_item(item):
    data_info = parse_perceptual_item_by_rules(item)
    return data_info


def parse_perceptual_data(perceptual_data_path):
    sheet_name = "感知点汇总表"
    perceptual_data_lst = load_jsons_from_xlsx_v2(xlsx_path=perceptual_data_path, sheet_name=sheet_name)[sheet_name]
    print("total perceptual data: {}".format(len(perceptual_data_lst)))
    #     for item in perceptual_data_lst:
    #         print((item["感知点"] or "") + ": " + (item["领域"] or ""))

    perceptual_data_dct = get_from_predefine_slot_info()
    perceptual_data_dct.update(get_from_manual_create())    # manual created by zhengyi and yuhan
    perceptual_data_dct.update(get_from_placeholder_info())     # added on 04/07
    perceptual_data_dct.update(get_from_adjust_info(perceptual_data_path))  # added on 04/07
    perceptual_data_dct.update(get_from_unity())
    for item in perceptual_data_lst:
        perceptual_data_dct.update(parse_perceptual_item(item))

    keys = list(perceptual_data_dct.keys())
    for key in keys:
        #         new_key = key.replace("'", "\\'")
        #         new_key = new_key.replace("\"", "\\'")
        new_key = key.replace("\"", "'")
        perceptual_data_dct[new_key] = perceptual_data_dct[key]

    return perceptual_data_dct, perceptual_data_lst


