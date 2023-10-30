# encoding=utf-8
# created @2023/10/30
# created by zhanzq
#

import os
import json
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup as BS
from common_utils.utils import format_string


class WEB:
    def __init__(self, url, proxies=None):
        self.url = url
        self.proxies = proxies
        self.html = None

    def download_file(self, output_dir):
        resp = requests.request("get", url=self.url, proxies=self.proxies)
        file_name = self.url.split("/")[-1]
        output_path = os.path.join(output_dir, file_name)
        with open(output_path, "wb") as writer:
            writer.write(resp.content)

        print(f"{file_name} has been downloaded, and stored in {output_dir}")
        return

    def download_web(self,):
        try:
            # 发起HTTP GET请求
            response = requests.get(self.url, proxies=self.proxies)

            # 检查请求是否成功
            if response.status_code == 200:
                # 获取网页源码
                html_content = response.text
                self.html = html_content
            else:
                print(f"请求失败，状态码：{response.status_code}")
        except requests.exceptions.RequestException as e:
            print("请求发生异常：", str(e))

        return

    def _get_item_by_text(self, father, text, res=[]):
        for child in father.children:
            if text in child.text:
                try:
                    if child.children is None:
                        res.append(child)
                    else:
                        self._get_item_by_text(child, text, res)
                except:
                    res.append(child)
        return

    def _get_item_by_text_in_div(self, text):
        bs = BS(self.html)
        divs = bs.find_all("div")
        res = []
        for div in divs:
            self._get_item_by_text(div, text, res)

        return res

    def _get_item_by_text_in_li(self, text):
        bs = BS(self.html)

        lis = bs.find_all("li")

        res = []
        for li in lis:
            self._get_item_by_text(li, text, res)

        return res

    def get_item_by_text(self, text):
        res = self._get_item_by_text_in_li(text)
        if not res:
            return self._get_item_by_text_in_div(text)
        else:
            return res

    @staticmethod
    def get_related_links(item, depth=5):
        links = set()
        for _ in range(depth):
            try:
                for a in item.find_all("a"):
                    links.add(a["href"])
            except:
                pass
            item = item.parent

        if links:
            print(format_string("related links"))
            for link in links:
                print(link)
        return links

    def get_item_by_href(self, href):
        if not self.html:
            self.download_web()
        bs = BS(self.html)
        lst = bs.find_all("a")
        for it in lst:
            if it["href"] == href:
                print(format_string("<a> attrs"))
                print(json.dumps(it.attrs, ensure_ascii=False, indent=4))
                return it

        return None

    def get_links_by_attr(self, **attr):
        if not self.html:
            self.download_web()

        bs = BS(self.html)

        lst = bs.find_all("a", **attr)
        links = []
        parsed_url = urlparse(self.url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        if lst:
            links = [base_url + it["href"] for it in lst]

        return links
