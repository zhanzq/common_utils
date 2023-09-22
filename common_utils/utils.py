# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# email : zhanzhiqiang09@126.com 
# date  : 2021/12/21
#

import re
import os

import time
from functools import wraps

import inspect
import hashlib
import subprocess
import random


def gen_add_or_sub_questions(top=10, min_val=1):
    """
    随机生成N以内的加减法示例，如 0 + 10 = , 10 - 2 =
    :param top: 算术上限N，默认值为10
    :param min_val: 算术下限，默认值为1
    :return: type, tuple(List, List, List), 返回所有可能的算术示例，分别为加法，减法，加减混合
    """
    add_lst = []
    sub_lst = []
    mix_lst = []
    for a in range(min_val, top+1):
        for b in range(min_val, top+1):
            if a + b > top:
                break
            c = a + b
            sub_lst.append(f"{c:2d} — {a:2d} = ")
            add_lst.append(f"{a:2d} + {b:2d} = ")

    mix_lst.extend(sub_lst)
    mix_lst.extend(add_lst)
    random.shuffle(add_lst)
    random.shuffle(sub_lst)
    random.shuffle(mix_lst)

    return add_lst, sub_lst, mix_lst


class Context:
    """
    Initialize the object with a dictionary.

    Args:
        d (dict): A dictionary to initialize the object with.
    """

    def __init__(self, *args, **kwargs):
        if args:
            self.__dict__.update(args[0])
        self.__dict__.update(kwargs)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getattr__(self, key):
        return self.__dict__[key]

    def __setattr__(self, key, value):
        self.__dict__[key] = value

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def pop(self, key):
        return self.__dict__.pop(key)

    def get(self, key):
        return self.__dict__.get(key)

    """
    Returns a string representation of the object's dictionary.

    Usage example:
    # Create a context object
    context = Context()

    # Print the string representation of the object's dictionary
    print(context.__str__())
    """

    def __str__(self):
        return str(self.__dict__)


def get_version(version_format="%m%d"):
    """
    根据日期格式返回当前日期对应的版本号
    :param version_format:
        %Y  Year with century as a decimal number.
        %m  Month as a decimal number [01,12].
        %d  Day of the month as a decimal number [01,31].
        %H  Hour (24-hour clock) as a decimal number [00,23].
        %M  Minute as a decimal number [00,59].
        %S  Second as a decimal number [00,61].
    :return:
    """

    return time.strftime(version_format)


def gen_id(string, len_id=8):
    md5 = hashlib.md5()
    md5.update(string.encode())
    return md5.hexdigest()[:len_id]


def _convert_to_str(arg):
    if type(arg) is str:
        return arg
    elif type(arg) is int or type(arg) is float or type(arg) is bool:
        return str(arg)
    elif callable(arg):
        return arg.__name__
    else:
        return type(arg).__name__


def time_cost(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        start_time = time.time()
        ret_res = f(*args, **kwargs)
        end_time = time.time()
        param_lst = []
        for arg in args:
            param_lst.append(_convert_to_str(arg))

        for key, val in kwargs.items():
            param_lst.append("{}={}".format(key, _convert_to_str(val)))
        params = ", ".join(param_lst)
        print("{}({}) cost time: {:.3f} seconds".format(f.__name__, params, end_time - start_time))
        return ret_res

    return decorated


def format_string(s, length=80):
    """
    format the print info of given string *s*
    :param s: which to format
    :param length: the output length, default 100
    :return: with format as follows:
    "*********************    hello, world!    **********************"
    """
    res = "   {}   ".format(s)
    left = (length - len(res)) // 2
    right = length - left - len(res)

    res = "{}{}{}".format("*" * left, res, "*" * right)

    return res


# 对比两个目录下所有的同名文件的差异
def diff_file(path1, path2, ignore_all_space=True, ignore_blank_lines=True, ignore_re=None):
    """
    compare two files use diff tool
    :param path1: the first file to compare
    :param path2: the second file to compare
    :param ignore_all_space: default True, ignore all whitespace, \t, \r, \n, \v, ' '
    :param ignore_blank_lines: default True, ignore blank lines
    :param ignore_re: default None, otherwise, skip the lines matched ignore_re
    :return: list, the compared result
    """
    output_lines = []
    # -T: pre pending a tab, -U0: unified context = 0 lines, -I re: use regex,
    # -w: ignore all space, -B: ignore blank lines
    whitespace_mark = " -w" if ignore_all_space else ""
    blank_line_mark = " -B" if ignore_blank_lines else ""
    re_exp = ' -I "{}"'.format(ignore_re) if ignore_re else ""
    cmd = "diff -dTU0{}{}{} {} {}".format(whitespace_mark, blank_line_mark, re_exp, path1, path2)
    file_name = path1.split("/")[-1]
    output_lines.append(format_string("diff {}".format(file_name)))
    output_lines.append(subprocess.getoutput(cmd))

    return output_lines


def diff_dir(dir_path1, dir_path2, output_path, ignore_all_space=True, ignore_blank_lines=True, ignore_re=None):
    """
    compare two dirs use diff tool
    :param dir_path1: the first dir to compare
    :param dir_path2: the second dir to compare
    :param output_path: the output path to store compared result
    :param ignore_all_space: default True, ignore all whitespace, \t, \r, \n, \v, ' '
    :param ignore_blank_lines: default True, ignore blank lines
    :param ignore_re: default None, otherwise, skip the lines matched ignore_re
    :return:
    """
    output_lines = []
    assert type(dir_path1) == type(dir_path2), "the compared files must both be dir or file"
    if os.path.isdir(dir_path1):
        file_lst1 = os.listdir(dir_path1)
        file_lst2 = os.listdir(dir_path2)
        for file_name in file_lst1:
            if file_name in file_lst2:
                path1 = os.path.join(dir_path1, file_name)
                path2 = os.path.join(dir_path2, file_name)
                output_lines.extend(diff_file(path1, path2, ignore_all_space, ignore_blank_lines, ignore_re))
    else:
        output_lines = diff_file(dir_path1, dir_path2, ignore_all_space, ignore_blank_lines, ignore_re)
    diff_info = "\n".join(output_lines)

    with open(output_path, "w") as writer:
        writer.write(diff_info)

    return


# parse the condition of each tts in formatted tpl
def get_indent_level(s, indent=4):
    """
    get indent level of input string s
    :param s: input string
    :param indent: whitespace num of one level, default 4
    :return:
    """
    l_space_num = len(s) - len(s.lstrip())

    return l_space_num // indent


def update_condition(line, condition_stk):
    """
    update condition stack
    :param line: input statement
    :param condition_stk: list, condition stack
    :return:
    """
    if_ptn = "^ *if *\((.*)\) *\{? *$"
    elif_ptn = "^ *}? *elif *\((.*)\) *\{? *$"
    else_ptn = "^ *}? *else *{ *$"

    level = get_indent_level(line, indent=4)
    if re.fullmatch(pattern=if_ptn, string=line):
        while len(condition_stk) > level:
            condition_stk.pop()
        if_cond = re.findall(if_ptn, line)[0]
        condition_stk.append([("if", if_cond)])
    elif re.fullmatch(pattern=elif_ptn, string=line):
        elif_cond = re.findall(elif_ptn, line)[0]
        while len(condition_stk) > level + 1:
            condition_stk.pop()
        condition_stk[-1].append(("elif", elif_cond))
    elif re.fullmatch(pattern=else_ptn, string=line):
        else_cond = []
        while len(condition_stk) > level + 1:
            condition_stk.pop()
        for item in condition_stk[-1]:
            else_cond.append("not {}".format(item[1]))
        condition_stk[-1].append(("else", " and ".join(else_cond)))
    else:
        pass


def parse_code_condition(format_codes):
    """
    parse formatted codes, and get the condition of each tts statement
    :param format_codes: the formatted codes to be parsed
    """
    condition_stk = []
    tts_ptn = "^ *(tts\(.*\));?$"
    codes = format_codes.split("\n")
    for line in codes:
        update_condition(line, condition_stk)
        if line.strip().startswith("tts("):
            tts = re.findall(pattern=tts_ptn, string=line)[0]
            condition = " and ".join([item[-1][1] for item in condition_stk])
            print("tts: {}, condition: {}".format(tts, condition))


def get_default_params(config_dct, func):
    args = {}
    args_set = set(inspect.getfullargspec(func).args)
    for key, val in config_dct.items():
        if key in args_set:
            args[key] = val

    return args
