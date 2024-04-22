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
    ptn = "(curl |-H |--header |--location |--data-raw |--data |--compressed|--insecure)"
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
                if data.startswith("'") or data.startswith("\""):
                    data = data[1:-1]
                    data = data.replace("false", "False").replace("true", "True").replace("null", "None")
                data = eval(data)  # 去除两端可能的'或者"
                if type(data) is dict:
                    return data
            except Exception as e:
                print(e)
                idx += 1
                continue
            # if data and "=" in data and "&" in data:
            if data and "=" in data:
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
    url_code = url_code.replace("--insecure", "")
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
    headers_str = json.dumps(headers, ensure_ascii=False, indent=4)
    headers_lst = headers_str.split("\n")
    headers_lst = ["    " + it for it in headers_lst]
    headers_str = "\n".join(headers_lst).strip()
    data = __extract_data(items)
    if type(data) is dict:
        data = json.dumps(data, indent=4, ensure_ascii=False)
        data_lst = data.split("\n")
        data_lst = ["    " + it for it in data_lst]
        data = "\n".join(data_lst).strip()

    codes = f"""
import requests
import json


def do_request():
    url = "{url}"
    headers = {headers_str}
    method = "GET"
    payload = ""
    data = {data}
    if data:
        payload = data
        method = "POST"

    response = requests.request(method, url, headers=headers, data=payload)
    obj_resp = json.loads(response.text)

    return obj_resp


do_request()


"""
    return codes


def main():
    curl_code = """curl 'https://aidev.haiersmarthomes.com/xuanwu-admin/jwt/domainIntent/add' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9' \
  -H 'Cache-Control: no-cache' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json;charset=UTF-8' \
  -H 'Cookie: visible=false; username=zhanzhiqiang; JSESSIONID=fac6c468-cb3a-4cfb-925f-45cf7dfb63db; rememberMe=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' \
  -H 'Origin: https://aidev.haiersmarthomes.com' \
  -H 'Pragma: no-cache' \
  -H 'Referer: https://aidev.haiersmarthomes.com/skills/upload/workbench/skillIndex.html' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36' \
  -H 'sec-ch-ua: "Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"' \
  -H 'sec-ch-ua-mobile: ?1' \
  -H 'sec-ch-ua-platform: "Android"' \
  --data-raw '{"id":"","domainCode":"IntegratedStove","intentCode":"openSpinWash","intentName":"打开自旋洗","commandCheckFlag":"N","statusQueryFlag":"N","functionQueryFlag":"N","functionStatusQueryFlag":"N","extend":"{}"}'"""

    code = convert_curl_to_python_request(curl_code)
    print(code)


if __name__ == "__main__":
    main()
