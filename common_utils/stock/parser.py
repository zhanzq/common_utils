# encoding=utf-8
# created @2024/10/17
# created by zhanzq
#

import os
import time
import requests
from common_utils.utils import color_string
from common_utils.text_io.txt import load_from_json


class StockParser:
    def __init__(self, stock_name_to_code_path=None):
        self.stock_name_to_code_path = stock_name_to_code_path
        self.stock_name_to_code = self.load_stock_name_to_code()

    def load_stock_name_to_code(self,):
        if self.stock_name_to_code_path is None:
            self.stock_name_to_code_path = "./stock_info.json"
            if not os.path.exists(self.stock_name_to_code_path):
                print(f"stock_info file '{self.stock_name_to_code_path}' not found in {os.path.curdir}")
                return {}
        stock_name_to_code = load_from_json(self.stock_name_to_code_path)

        return stock_name_to_code

    def get_stock_info(self, stock_code_or_name):
        stock_code_list = []
        for code_or_name in  stock_code_or_name.split(","):
            stock_code = self.stock_name_to_code.get(code_or_name, code_or_name)
            if len(stock_code) == 6:
                stock_code = self.get_exchange(stock_code) + stock_code  # 默认为上证
            elif len(stock_code) == 5:
                stock_code = "hk" + stock_code
            stock_code_list.append(stock_code)

        url = f"https://hq.sinajs.cn/list={','.join(stock_code_list)}"
        headers = {
            'Referer': 'https://finance.sina.com.cn',
            'Content-Type': 'application/json'
        }

        response = requests.get(url, headers=headers)

        return response.text.strip()

    @staticmethod
    def parse_a_stock_info(stock_info):
        if stock_info is None:
            return
        s = stock_info.split('"')[1]
        items = s.split(",")

        name = items[0]
        _open, _close, _curr, _top, _low = [float(items[i]) for i in range(1, 6)]
        #     price_buy1 = items[6] # items[11]
        #     price_sell1 = items[7]
        deal_num = int(items[8]) / 100.
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
            "deal_num": deal_num,
            "deal_amount": deal_amount,
            "buy": buy_info,
            "sell": sell_info,
            "date": _date,
            "time": _time
        }

        return info

    @staticmethod
    def get_exchange(stock_code: str) -> str:
        """
        根据A股股票代码判断交易所

        返回：
            SH - 上海证券交易所
            SZ - 深圳证券交易所
            UNKNOWN - 无法判断
        """
        code = str(stock_code).strip()

        if code.startswith(("600", "601", "603", "605", "688", "689")):
            return "sh"

        if code.startswith(("000", "001", "002", "003", "300", "301")):
            return "sz"

        return "sh"

    @staticmethod
    def parse_hk_stock_info(stock_info):
        if stock_info is None:
            return
        s = stock_info.split('"')[1]
        items = s.split(",")

        name = items[1]
        _open, _close, _top, _low, _curr = [float(items[i]) for i in range(2, 7)]
        deal_num = int(items[12]) / 100.  # 成交量
        deal_amount = float(items[11]) / 10000.  # 成交额
        delta_amount = float(items[7])    # 涨跌
        delta_rate = float(items[8])      # 涨幅
        buy_info = [float(items[9])]
        sell_info = [float(items[10])]

        # ppm = float(items[13])  # 市盈率
        # week_ratio = float(items[14])  # 周息率
        year_high = float(items[15])
        year_low = float(items[16])
        _date = items[17]
        _time = items[18]
        info = {
            "name": name,
            "open": _open,
            "close": _close,
            "curr": _curr,
            "top": _top,
            "low": _low,
            "deal_num": deal_num,
            "deal_amount": deal_amount,
            "buy": buy_info,
            "sell": sell_info,
            "delta_amount": delta_amount,
            "delta_rate": delta_rate,
            "year_high": year_high,
            "year_low": year_low,
            "date": _date,
            "time": _time
        }

        return info

    def parse_stock_info(self, stock_info):
        if stock_info is None:
            return
        elif stock_info.startswith("var hq_str_hk"):
            return self.parse_hk_stock_info(stock_info)
        else:
            return self.parse_a_stock_info(stock_info)

    @staticmethod
    def print_stock_info(stock_info):
        if stock_info is None:
            return
        price_curr, buy1, sell1 = stock_info["curr"], stock_info["buy"][0], stock_info["sell"][0]
        name = stock_info["name"]
        print_info = f"{price_curr} {color_string(s=buy1, color='red')} {color_string(s=sell1, color='green')}"
        print(f"{name}: {print_info:100s}", end="\r")


def main():
    stock_parser = StockParser()

    stock_info = stock_parser.get_stock_info(stock_code_or_name="513050")
    print(stock_info)
    stock_info = stock_parser.parse_stock_info(stock_info)
    stock_parser.print_stock_info(stock_info)

    return


if __name__ == "__main__":
    main()
