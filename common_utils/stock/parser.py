# encoding=utf-8
# created @2024/10/17
# created by zhanzq
#

import requests
from common_utils.utils import color_string


def get_stock_info(stock_code):
    if len(stock_code) == 6:
        stock_code = "sz" + stock_code  # 默认为上证
    url = f"https://hq.sinajs.cn/list={stock_code}"

    payload = ""
    headers = {
        'Referer': 'https://finance.sina.com.cn',
        'Content-Type': 'application/json'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    return response.text


def parse_stock_info(stock_info):
    s = stock_info.split('"')[1]
    items = s.split(",")
    name = items[0]
    _open, _close, _curr, _top, _low = [float(items[i]) for i in range(1, 6)]
    #     price_buy1 = items[6] # items[11]
    #     price_sell1 = items[7]
    deal_num = int(items[8]) / 100
    deal_amount = float(items[9]) / 10000.
    buy_info = [(int(items[i]), float(items[i + 1])) for i in range(10, 20, 2)]
    sell_info = [(int(items[i]), float(items[i + 1])) for i in range(20, 30, 2)]
    _date = items[30]
    _time = items[31]
    info = {
        "name": name,
        "open": _open,
        "close": _close,
        "curr": _curr,
        "top": _top,
        "low": _low,
        "buy": buy_info,
        "sell": sell_info,
        "date": _date,
        "time": _time
    }

    return info


def print_stock_info(stock_info):
    price_curr, buy1, sell1 = stock_info["curr"], stock_info["buy"][0], stock_info["sell"][0]
    name = stock_info["name"]
    print_info = f"{price_curr} {color_string(s=buy1, color='red')} {color_string(s=sell1, color='green')}"
    print(f"{name}: {print_info:100s}", end="\r")


def main():
    code = "002459"
    stock_info = get_stock_info(stock_code=code)
    stock_info = parse_stock_info(stock_info)
    print_stock_info(stock_info)

    return


if __name__ == "__main__":
    main()
