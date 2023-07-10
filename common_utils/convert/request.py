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
    ptn = "(-H|--header|--location|--data|--data-raw)"
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
            except:
                pass
            out.update(json.loads(data))
            idx += 2
        else:
            idx += 1

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
    flags = ["--location"]
    for flag in flags:
        if s.startswith(flag):
            return True

    return False


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
        payload = json.dumps(data)
        method = "POST"

    response = requests.request(method, url, headers=headers, data=payload)

    obj_resp = json.loads(response.text)
    print(obj_resp)

    return obj_resp


def test():
    print(do_request())


test()

"""
    return codes


def main():
    curl_code = """curl 'https://aidev.haiersmarthomes.com/xuanwu-admin/jwt/workbench/categoryList?pageNum=1&pageSize=10' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9' \
  -H 'Connection: keep-alive' \
  -H 'Cookie: JSESSIONID=8c0518ad-1d95-4154-ae8d-7a73fa3aca47; rememberMe=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' \
  -H 'Referer: https://aidev.haiersmarthomes.com/skills/upload/workbench/skillIndex.html' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  --compressed"""

    code = convert_curl_to_python_request(curl_code)
    print(code)


if __name__ == "__main__":
    main()
