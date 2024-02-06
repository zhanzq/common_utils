# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# date  : 2023/7/4
#


import re
import json


def __parse_curl_code(curl_code):
    # replace format char
    curl_code = re.sub(string=curl_code, pattern="\s", repl=" ")
    ptn = "(curl |-H |--header |--location |--data-raw |--data |--compressed)"
    items = re.split(string=curl_code, pattern=ptn)

    return items


def __is_data(s):
    flags = ["--data", "--data-raw"]
    for flag in flags:
        if s.startswith(flag):
            return True

    return False


def __extract_data(items):
    out = {}
    idx = 0
    sz = len(items)

    while idx < sz:
        if __is_data(items[idx]):
            data = items[idx + 1]
            try:
                data = data.strip()
                data = eval(data)  # 去除两端可能的'或者"
            except Exception as e:
                print(e)
                idx += 1
                continue
            if data and "=" in data and "&" in data:
                return data
            else:
                out.update(json.loads(data))
            break
        else:
            idx += 1

    if not out:
        return ""
    else:
        return out


def __is_header(s):
    flags = ["-H", "--header"]
    for flag in flags:
        if s.startswith(flag):
            return True

    return False


def __extract_headers(items):
    headers = {}
    idx = 0
    sz = len(items)

    while idx < sz:
        if __is_header(items[idx]):
            header = items[idx + 1]
            try:
                header = header.strip()
                header = eval(header)  # 去除两端可能的'或者"
            except:
                pass
            key, val = header.split(": ")
            headers[key] = val
            idx += 2
        else:
            idx += 1

    return headers


def __is_url(s):
    flags = ["curl"]
    for flag in flags:
        if s.startswith(flag):
            return True

    return False


def __preprocess_url_code(url_code):
    url_code = url_code.replace("--location", "")
    url_code = url_code.replace("--compressed", "")
    return url_code


def __extract_url(items):
    url = ""
    idx = 0
    sz = len(items)

    while idx < sz:
        if __is_url(items[idx]):
            tmp = items[idx + 1]
            try:
                tmp = tmp.strip()
                tmp = eval(tmp)
            except:
                pass
            url = tmp
            break
        else:
            idx += 1

    return url


def convert_curl_to_python_request(curl_code):
    if not curl_code:
        return ""
    items = __parse_curl_code(curl_code)
    url = __extract_url(items)
    headers = __extract_headers(items)
    data = __extract_data(items)
    if type(data) is dict:
        data = "\"\"\"{json.dumps(data, indent=4, ensure_ascii=False)}\"\"\""

    codes = f"""
import requests
import json


def do_request():
    url = "{url}"

    headers = {json.dumps(headers, ensure_ascii=False, indent=4)}
    method = "GET"
    payload = ""
    data = "{data}"
    if data:
        payload = data
        method = "POST"

    response = requests.request(method, url, headers=headers, data=payload)

    obj_resp = json.loads(response.text)
    print(obj_resp)

    return obj_resp


do_request()


"""
    return codes


def main():
    curl_code = """curl 'https://aidev.haiersmarthomes.com/xuanwu-admin/ver/deployTask/add' \
  -H 'Accept: application/json, text/javascript, */*; q=0.01' \
  -H 'Accept-Language: zh-CN,zh;q=0.9' \
  -H 'Cache-Control: no-cache' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
  -H 'Cookie: visible=false; username=zhanzhiqiang; JSESSIONID=29d20a79-0348-4a78-8a72-daa6216d1a54; rememberMe=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' \
  -H 'Origin: https://aidev.haiersmarthomes.com' \
  -H 'Pragma: no-cache' \
  -H 'Referer: https://aidev.haiersmarthomes.com/xuanwu-admin/ver/deployTask/add' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'sec-ch-ua: "Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  --data-raw 'version=2.62.72&remark=fb' \
  --compressed"""

    code = convert_curl_to_python_request(curl_code)
    print(code)


if __name__ == "__main__":
    main()
