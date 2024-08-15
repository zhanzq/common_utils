# encoding=utf-8
# created @2024/3/18
# created by zhanzq
#
import re

import requests
import json
from urllib.request import quote
from common_utils.const.web import USER_AGENT, COOKIE_XUANWU_DEV


def get_word_dict_in_xuanwu(dict_code, env="dev"):
    """
    查看玄武字典dict_code中的所有词语信息
    :param dict_code: 玄武字典代码
    :param env: 玄武环境，默认为dev开发环境
    :return:
    """
    url = {
        "dev": "https://aidev.haiersmarthomes.com/xuanwu-admin/nlp/dictWord/list",
        "service": "https://aiservice.haier.net/xuanwu-admin/nlp/dictWord/list",
    }[env]
    cookie = {
        "dev": COOKIE_XUANWU_DEV
    }[env]
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": cookie,
        "User-Agent": USER_AGENT,
        "X-Requested-With": "XMLHttpRequest",
    }
    method = "POST"
    payload = f"dictCode={dict_code}&word=&synonym=&pageSize=1000&pageNum=1&orderByColumn=&isAsc=asc"

    response = requests.request(method, url, headers=headers, data=payload)

    obj_resp = json.loads(response.text)

    word_dict = {}
    for item in obj_resp["rows"]:
        normed_word = item.get("word")
        out_item = {
            "id": item.get("id"),
            "word": normed_word,
            "synonym": item.get("synonym")
        }
        word_dict[normed_word] = out_item

    return word_dict, obj_resp


def search_word_in_xuanwu_dict(dict_code, word):
    """
    在给定的玄武字典中查找词语word
    :param dict_code: 玄武字典代码
    :param word: 待查找词语
    :return: 未找到则返回None, 否则返回{"id": ID, "word": KEY, "synonym": SYNONYM}
    """
    word_dct, _ = get_word_dict_in_xuanwu(dict_code)

    if word in word_dct:
        return word_dct[word]
    else:
        for normed_word in word_dct:
            synonym = word_dct[normed_word]["synonym"]
            if synonym and word in synonym.split(","):
                return word_dct[normed_word]

    return None


def add_word_to_xuanwu_dict(dict_code, word, synonym=""):
    """
    向玄武字典中添加关键词
    :param dict_code: 玄武字典代码
    :param word: 关键词
    :param synonym: 关键词对应的泛化说法，默认为空
    :return:
    """
    url = "https://aidev.haiersmarthomes.com/xuanwu-admin/nlp/dictWord/add"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": COOKIE_XUANWU_DEV,
        "User-Agent": USER_AGENT,
        "X-Requested-With": "XMLHttpRequest",
    }

    word_dct, _ = get_word_dict_in_xuanwu(dict_code)
    if word in word_dct:
        print(f"'{word}' already exists in dict '{dict_code}'")
        return

    method = "POST"
    payload = f"dictCode={dict_code}&word={quote(word)}&synonym={quote(synonym)}"

    response = requests.request(method, url, headers=headers, data=payload)

    obj_resp = json.loads(response.text)
    print(f"add '{word}': '{synonym}' into '{dict_code}'")

    return obj_resp


def edit_xuanwu_dict(dict_code, word, synonym, overwrite=False):
    """
    添加或修改玄武字典中关键词的泛化说法
    :param dict_code: 玄武字典代码
    :param word: 关键词
    :param synonym: 关键词对应的泛化说法
    :param overwrite: 是否重写，默认不重写，即在原有词的基础上追加泛化词
    :return:
    """
    url = "https://aidev.haiersmarthomes.com/xuanwu-admin/nlp/dictWord/edit"

    headers = {
        "Cookie": COOKIE_XUANWU_DEV,
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest"
    }

    word_dict, _ = get_word_dict_in_xuanwu(dict_code)

    if word not in word_dict:
        return add_word_to_xuanwu_dict(dict_code=dict_code, word=word, synonym=synonym)

    new_synonym = word_dict[word]["synonym"]
    old_lst = [] if not new_synonym else new_synonym.split(",")
    if type(synonym) is str:
        # 支持分隔符：/,，;；|和\
        lst = re.split(pattern="/|,|，|;|；|\\||\\\\", string=synonym)
        lst = [it.strip() for it in lst]
    else:
        lst = synonym

    if not overwrite:
        lst.extend(old_lst)
        lst = list(set(lst))
    print(lst)

    method = "POST"
    payload = f"id={word_dict[word]['id']}&dictCode={dict_code}&word={quote(word)}&synonym={quote(','.join(lst))}"

    response = requests.request(method, url, headers=headers, data=payload)

    obj_resp = json.loads(response.text)

    return obj_resp


def add_dict_in_xuanwu(dict_code, dict_name, parent_code=0, dict_type="ENUM", dict_category="OTHER"):
    """
    向玄武系统中新增字典
    :param dict_code: 玄武字典代码
    :param dict_name: 字典名称
    :param parent_code: 父节点代码，默认为0
    :param dict_type: 字典类型，默认为ENUM，枚举类型
    :param dict_category: 字典分类，默认为OTHER
    :return:
    """
    url = "https://aidev.haiersmarthomes.com/xuanwu-admin/nlp/dictionary/add"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        # "Cookie": "JSESSIONID=9a4d7b0c-b390-43e5-b6cc-e4e9740d7277; rememberMe=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",
        "Cookie": COOKIE_XUANWU_DEV,
        "User-Agent": USER_AGENT,
        "X-Requested-With": "XMLHttpRequest",
    }
    method = "POST"
    payload = (f"dictCode={dict_code}&dictName={quote(dict_name)}&parentCode={parent_code}&dictType={dict_type}"
               f"&dictCategory={dict_category}")

    response = requests.request(method, url, headers=headers, data=payload)
    obj_resp = json.loads(response.text)

    return obj_resp


def remove_word_from_dict_in_xuanwu(dict_code, word):
    """

    :param dict_code:
    :param word:
    :return:
    """
    url = "https://aidev.haiersmarthomes.com/xuanwu-admin/nlp/dictWord/remove"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        # "Cookie": "JSESSIONID=9a4d7b0c-b390-43e5-b6cc-e4e9740d7277; rememberMe=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",
        "Cookie": COOKIE_XUANWU_DEV,
        "User-Agent": USER_AGENT,
        "X-Requested-With": "XMLHttpRequest",
    }
    word_dct, _ = get_word_dict_in_xuanwu(dict_code=dict_code, env="dev")
    if word not in word_dct:
        print(f"word {word} not in {dict_code}")
        return None
    else:
        word_id = word_dct[word]["id"]
    method = "POST"
    payload = f"ids={word_id}"
    response = requests.request(method, url, headers=headers, data=payload)
    obj_resp = json.loads(response.text)

    return obj_resp


def main():
    # add word dict
    res_info = add_dict_in_xuanwu(dict_code="english_song", dict_name="英文歌名称")
    print(res_info)

    # show word dict
    dict_code = "sys@integratedStove_mode"
    word_dct, _ = get_word_dict_in_xuanwu(dict_code=dict_code, env="service")
    print(json.dumps(word_dct, indent=4, ensure_ascii=False))

    # search word in dict
    search_word = "设置"
    found = search_word_in_xuanwu_dict(dict_code=dict_code, word=search_word)
    if found:
        print(json.dumps(found, indent=4, ensure_ascii=False))
    else:
        print(f"在字典 '{dict_code}' 中未找到 '{search_word}'")

    # add word into dict
    word = "设为"
    add_info = add_word_to_xuanwu_dict(dict_code=dict_code, word=word)


if __name__ == "__main__":
    main()
