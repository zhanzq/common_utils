# encoding=utf-8
# created @2024/3/18
# created by zhanzq
#

import requests
import json
from urllib.request import quote


def get_word_dict_in_xuanwu(dict_code):
    """
    查看玄武字典dict_code中的所有词语信息
    :param dict_code: 玄武字典代码
    :return:
    """
    url = "https://aidev.haiersmarthomes.com/xuanwu-admin/nlp/dictWord/list"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": "JSESSIONID=9acb1626-8c2f-439c-b869-3d29b8e39773; rememberMe=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",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
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
            if synonym and word in synonym:
                return word_dct[normed_word]

        for normed_word in word_dct:
            if word in normed_word:
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
        "Cookie": "JSESSIONID=9acb1626-8c2f-439c-b869-3d29b8e39773; rememberMe=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",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
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


def edit_xuanwu_dict(dict_code, word, synonym):
    """
    添加或修改玄武字典中关键词的泛化说法
    :param dict_code: 玄武字典代码
    :param word: 关键词
    :param synonym: 关键词对应的泛化说法
    :return:
    """
    url = "https://aidev.haiersmarthomes.com/xuanwu-admin/nlp/dictWord/edit"

    headers = {
        "Cookie": "JSESSIONID=02a4405f-c8fd-47ed-94ec-dbcb1ad0af04; rememberMe=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",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest"
    }

    word_dict, _ = get_word_dict_in_xuanwu(dict_code)

    if word not in word_dict:
        return add_word_to_xuanwu_dict(dict_code=dict_code, word=word, synonym=synonym)

    new_synonym = word_dict[word]["synonym"]
    lst = [] if not new_synonym else new_synonym.split(",")
    if type(synonym) is str:
        lst = synonym.split(",")
    else:
        lst = synonym

    print(lst)

    method = "POST"
    payload = f"id={word_dict[word]['id']}&dictCode={dict_code}&word={quote(word)}&synonym={quote(','.join(lst))}"

    response = requests.request(method, url, headers=headers, data=payload)

    obj_resp = json.loads(response.text)

    return obj_resp


def main():
    # show word dict
    dict_code = "set_to"
    word_dct, _ = get_word_dict_in_xuanwu(dict_code=dict_code)
    print(json.dumps(word_dct, indent=4, ensure_ascii=False))

    # search word in dict
    found = search_word_in_xuanwu_dict(dict_code=dict_code, word="设置为")
    if found:
        print(json.dumps(found, indent=4, ensure_ascii=False))
    else:
        print(found)

    # add word into dict
    word = "设为"
    add_info = add_word_to_xuanwu_dict(dict_code=dict_code, word=word)


if __name__ == "__main__":
    main()
