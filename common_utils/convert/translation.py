# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# date  : 2023/7/14
#

import re
import html
from urllib import parse
import requests

import time
import json
import random
import hashlib

from Crypto.Cipher import AES
import base64
from Crypto.Util.Padding import unpad


def __normalize_google_translation_language(language):
    dct = {
        "zh-CN": ["zh-CN", "中文", "中", "汉语", "中语"],
        "en": ["en", "英文", "英语", "英"]
    }

    lan_dct = {}
    for norm_val, lst in dct.items():
        for lan in lst:
            lan_dct[lan] = norm_val

    return lan_dct.get(language, language)


def __normalize_youdao_translation_language(language):
    dct = {
        "zh-CHS": ["zh-CHS", "zh-CN", "中文", "中", "汉语", "中语"],
        "en": ["en", "英文", "英语", "英"]
    }

    lan_dct = {}
    for norm_val, lst in dct.items():
        for lan in lst:
            lan_dct[lan] = norm_val

    return lan_dct.get(language, language)


def _translate_with_google(text, from_language="en", to_language="zh-CN", tries=0):
    to_language = __normalize_google_translation_language(language=to_language)
    from_language = __normalize_google_translation_language(language=from_language)
    google_translate_url = 'http://translate.google.com/m?q=%s&tl=%s&sl=%s'
    try:
        # time.sleep(3)
        text = parse.quote(text)
        url = google_translate_url % (text, to_language, from_language)
        proxy = {
            "http": "http://127.0.0.1:1087",
        }
        response = requests.get(url, proxies=proxy)
        data = response.text
        expr = r'(?s)class="(?:t0|result-container)">(.*?)<'
        result = re.findall(expr, data)
        if len(result) == 0:
            return ""

        return html.unescape(result[0])
    except:
        tries += 1
        if tries >= 3:
            return ""
        else:
            return _translate_with_google(text, from_language, to_language, tries + 1)


def _translate_youdao_v1(text, from_language="中文", to_language="英文", tries=0):
    time.sleep(3)
    # 有道词典 api
    url = 'http://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule&smartresult=ugc&sessionFrom=null'
    # 传输的参数，其中 i 为需要翻译的内容
    key = {
        'type': "AUTO",
        'i': text,
        "doctype": "json",
        "version": "2.1",
        "keyfrom": "fanyi.web",
        "ue": "UTF-8",
        "action": "FY_BY_CLICKBUTTON",
        "typoResult": "true"
    }
    try:
        # key 这个字典为发送给有道词典服务器的内容
        response = requests.post(url, data=key)
        # 判断服务器是否相应成功
        if response.status_code == 200:
            # 然后相应的结果
            result = json.loads(response.text)
            result = result['translateResult'][0][0]['tgt']
            return result
    except:
        tries += 1
        if tries >= 3:
            return ""
        else:
            return _translate_youdao_v1(text, from_language, to_language, tries)


def _translate_youdao_v3(text, from_language="en", to_language="zh-CHS", tries=0):
    # 获取Cookie的路径为https://fanyi.youdao.com/index.html#/
    # 找到网络中的webtranslate请求对应的Cookie即可
    url = 'https://fanyi.youdao.com/bbk/translate_m.do'
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Host': 'fanyi.youdao.com',
        'Origin': 'https://fanyi.youdao.com',
        'Referer': 'https://fanyi.youdao.com/index.html',
        'Cookie': 'OUTFOX_SEARCH_USER_ID=1354904997@10.105.253.24; OUTFOX_SEARCH_USER_ID_NCOO=1625245685.750373; P_INFO=zhanzhiqiang09@126.com|1689316897|1|dict_logon|11&17|bej&1687835220&mail126#not_found&null#10#0#0|&0|mail126|zhanzhiqiang09@126.com; DICT_LOGIN=8||1689320439922; DICT_FORCE=true',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="8"',
        'sec-ch-ua-mobile': '?0',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/92.0.4515.131 Safari/537.36 SLBrowser/8.0.0.2242 SLBChan/25',
    }

    # 'ts':   '1680404913064',  ==> 13位 当前时间戳
    # 'salt': '16804049130648', ==> 13位 当前时间戳 + [0,9] 的一个随机整数
    # 'sign': 'e9c74c82dbb3ca3f1d25f0a743647a8d', ==> md5  La(Na + e + n + Va);

    #  Na -> "fanyideskweb"
    #  e -> translation_words
    #  n -> salt
    #  Va -> "Ygy_4c=r#e#4EX^NUGUc5"

    ts = str(int(time.time() * 1000))
    salt = ts + str(random.randrange(0, 10))
    # md5 -> 编码 -> 转16进制 数据字符串
    sign = hashlib.md5(("fanyideskweb" + text + salt + "Ygy_4c=r#e#4EX^NUGUc5").encode('utf-8')).hexdigest()

    form_data = {
        'i': text,

        'from': 'zh-CHS',
        'to': 'en',
        'client': 'fanyideskweb',
        'bv': '655f7a3056df1c2a1fccf338154a4eaf',
        'doctype': 'json',
        'version': '3.0',
        'cache': 'true',
        'ts': ts,
        'salt': salt,
        'sign': sign,

    }
    try:
        res = requests.post(url=url, headers=headers, data=form_data).json()

        # resp = [i['tgt'] for i in res['translateResult']]
        resp = res["translateResult"][0]["tgt"]
        return resp
    except:
        tries += 1
        if tries > 3:
            return ""
        else:
            return _translate_youdao_v3(text, from_language, to_language, tries)


def decrypt(decrypt_str):
    key = "ydsecret://query/key/B*RGygVywfNBwpmBaZg*WT7SIOUP2T0C9WHMZN39j^DAdaZhAnxvGcCY6VYFwnHl"
    iv = "ydsecret://query/iv/C@lZe2YzHtZ2CYgaXKSVfsb7Y4QWHjITPPZ0nQp87fBeJ!Iv6v^6fvi2WN@bYpJ4"

    key_md5 = hashlib.md5(key.encode('utf-8')).digest()
    iv_md5 = hashlib.md5(iv.encode('utf-8')).digest()
    aes = AES.new(key=key_md5, mode=AES.MODE_CBC, iv=iv_md5)

    code = aes.decrypt(base64.urlsafe_b64decode(decrypt_str))
    return unpad(code, AES.block_size).decode('utf8')


def _translate_youdao_v4(text, from_language="中文", to_language="英文", tries=0):
    url = 'https://dict.youdao.com/webtranslate'
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'OUTFOX_SEARCH_USER_ID_NCOO=379056539.64209586; OUTFOX_SEARCH_USER_ID=-380628258@222.182.116.19',
        'Host': 'dict.youdao.com',
        'Origin': 'https://fanyi.youdao.com',
        'Referer': 'https://fanyi.youdao.com/',
        'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/111.0.0.0 Safari/537.36',
    }

    # 'ts':   '1680404913064',  ==> 13位 当前时间戳
    # fsdsogkndfokasodnaso 固定值

    ts = str(int(time.time() * 1000))
    str_sign = f"client=fanyideskweb&mysticTime={ts}&product=webfanyi&key=fsdsogkndfokasodnaso"
    sign = hashlib.md5(str_sign.encode('utf-8')).hexdigest()

    form_data = {
        'i': text,
        'from': 'auto',
        'to': '',
        'sign': sign,
        'dictResult': 'true',
        'keyid': 'webfanyi',
        'client': 'fanyideskweb',
        'product': 'webfanyi',
        'appVersion': '1.0.0',
        'vendor': 'web',
        'pointParam': 'client,mysticTime,product',
        'mysticTime': ts,
        'keyfrom': 'fanyi.web',
    }

    try:
        decrypt_str = requests.post(url=url, headers=headers, data=form_data).text
        end_code = decrypt(decrypt_str)
        json_data = json.loads(end_code)
        res = json_data['translateResult'][0][0]["tgt"]
        return res
    except:
        tries += 1
        if tries >= 3:
            return ""
        else:
            return _translate_youdao_v4(text, from_language, to_language, tries)


def translate(text, channel="google", version="v1", from_language="中", to_language="英"):
    if channel.lower() == "google":
        return _translate_with_google(text=text, from_language=from_language, to_language=to_language)
    elif channel.lower() == "youdao":
        if version == "v1":
            return _translate_youdao_v1(text=text, from_language=from_language, to_language=to_language)
        elif version == "v3":
            return _translate_youdao_v3(text=text, from_language=from_language, to_language=to_language)
        elif version == "v4":
            return _translate_youdao_v4(text=text, from_language=from_language, to_language=to_language)
        else:
            return _translate_youdao_v3(text=text, from_language=from_language, to_language=to_language)
    else:
        return ""


def main():
    text = "你好呀"
    out = translate(text, channel="youdao", from_language="中", to_language="英")
    print(out)

    pass


if __name__ == "__main__":
    main()
