# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# date  : 2023/7/4
#

import shlex
import json
from urllib.parse import urlparse, parse_qsl

# 需要过滤的浏览器头（非常关键）
BROWSER_BLACKLIST_HEADERS = {
    "host",
    "content-length",
    "connection",
    "origin",
    "referer",
    "sec-fetch-site",
    "sec-fetch-mode",
    "sec-fetch-dest",
    "sec-fetch-user",
    "sec-ch-ua",
    "sec-ch-ua-mobile",
    "sec-ch-ua-platform",
    "accept",
    "accept-language",
    "cache-control",
    "pragma",
}


def _clean_multiline(curl_code: str) -> str:
    """去掉 \\ 换行"""
    lines = [line.strip() for line in curl_code.strip().splitlines()]
    merged = ""
    for line in lines:
        if line.endswith("\\"):
            merged += line[:-1] + " "
        else:
            merged += line + " "
    return merged.strip()


def _parse_curl(curl_code: str):
    curl_code = _clean_multiline(curl_code)
    tokens = shlex.split(curl_code)

    if tokens[0].lower() != "curl":
        raise ValueError("Not a curl command")

    method = None
    url = None
    headers = {}
    data = None
    params = {}

    i = 1
    while i < len(tokens):
        token = tokens[i]

        # URL
        if not token.startswith("-") and url is None:
            url = token

        # Method
        elif token in ("-X", "--request"):
            method = tokens[i + 1].upper()
            i += 1

        # Headers
        elif token in ("-H", "--header"):
            header = tokens[i + 1]
            i += 1
            if ":" in header:
                k, v = header.split(":", 1)
                k = k.strip()
                v = v.strip()

                # 过滤浏览器头
                if k.lower() in BROWSER_BLACKLIST_HEADERS:
                    continue

                # 默认不带 Cookie（安全）
                if k.lower() == "cookie":
                    continue

                headers[k] = v

        # Data
        elif token.startswith("--data") or token in ("-d", "--data-raw", "--data-binary", "--data-urlencode"):
            data = tokens[i + 1]
            i += 1

        i += 1

    # 如果没有 method
    if method is None:
        method = "POST" if data else "GET"

    # 解析 URL 参数
    parsed = urlparse(url)
    if parsed.query:
        params = dict(parse_qsl(parsed.query))
        url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    return method, url, headers, data, params


def _detect_json(data: str):
    if not data:
        return None, False
    try:
        return json.loads(data), True
    except Exception:
        return data, False


def _indent_block(text: str, spaces: int = 4) -> str:
    """给多行文本整体增加缩进"""
    if not text:
        return ""
    prefix = " " * spaces
    return "\n".join(prefix + line if line.strip() else line
                     for line in text.splitlines())


def _dict_to_code(name: str, value: dict, base_indent: int = 4) -> str:
    """
    生成漂亮且正确缩进的 dict Python 代码
    """
    indent = " " * base_indent

    if not value:
        return f"{indent}{name} = None"

    dumped = json.dumps(value, indent=4, ensure_ascii=False)
    lines = dumped.splitlines()

    # 第一行：headers = {
    code_lines = [f"{indent}{name} = {lines[0]}"]

    # 中间行：保持json自身缩进 + 函数体缩进
    for line in lines[1:]:
        code_lines.append(f"{indent}{line}")

    return "\n".join(code_lines)



def convert_curl_to_python_request(curl_code: str) -> str:
    method, url, headers, data, params = _parse_curl(curl_code)
    payload, is_json = _detect_json(data)

    headers_code = _dict_to_code("headers", headers)
    params_code = _dict_to_code("params", params)

    if is_json:
        payload_code = _dict_to_code("json_data", payload)
        send_line = "response = session.request(method, url, headers=headers, params=params, json=json_data)"
    elif payload:
        payload_code = f'data = {repr(payload)}'
        send_line = "response = session.request(method, url, headers=headers, params=params, data=data)"
    else:
        payload_code = "data = None"
        send_line = "response = session.request(method, url, headers=headers, params=params)"

    send_line = " "*8 + send_line.strip()

    code = f'''import requests
import json


def do_request():
    method = "{method}"
    url = "{url}"

{headers_code}

{params_code}

{payload_code}

    session = requests.Session()

    try:
{send_line}
        response.raise_for_status()
    except requests.RequestException as e:
        print("Request Failed:", e)
        return None

    try:
        return response.json()
    except ValueError:
        return response.text
'''

    return code


def load_curl_from_file(file_path: str) -> str:
    """
    从文件完整读取 curl 命令（保持原始格式）
    支持 UTF-8 / Windows / Mac / Linux
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            raise ValueError("curl_test_data.txt 是空文件")

        return content

    except FileNotFoundError:
        raise FileNotFoundError(f"未找到文件: {file_path}")
    except Exception as e:
        raise RuntimeError(f"读取 curl 文件失败: {e}")

def main():
    curl_code = load_curl_from_file("curl_test_data.txt")
    code = convert_curl_to_python_request(curl_code)
    print(code)


if __name__ == "__main__":
    main()
