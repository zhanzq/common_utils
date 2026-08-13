# encoding=utf-8
# created @2023/10/30
# created by zhanzq
#

import os
import json
import requests
from urllib.parse import urlparse
from bs4.element import NavigableString
from common_utils.utils import format_string
from common_utils.const.web import USER_AGENT
from bs4 import BeautifulSoup as BS
import chardet


class WEB:
    def __init__(self, url, refer=None, proxies=None):
        self.url = url
        self.headers = {"user-agent": USER_AGENT}
        if refer:
            self.headers["Referer"] = refer
        self.proxies = proxies
        # 如果后缀为一个文件，如.mp3，则不执行download_web
        if "." not in url.split("/")[-1]:
            self.html = self.download_web()
            self.bs = BS(self.html, features="html.parser")
        else:
            self.html = None
            self.bs = None

    def download_file(self, output_dir, file_name=None):
        """
        下载文件
        :param output_dir:
        :param file_name:
        :return:
        """
        os.makedirs(output_dir, exist_ok=True)
        resp = requests.request("get", url=self.url, headers=self.headers, proxies=self.proxies)
        if not file_name:
            file_name = self.url.split("/")[-1]
        else:
            # 使用解析出来的后缀名
            file_name = file_name.split(".")[0] + "." + self.url.split(".")[-1]
        output_path = os.path.join(output_dir, file_name)
        sz = len(resp.content)
        with open(output_path, "wb") as writer:
            writer.write(resp.content)

        print(f"{file_name}: ({sz} bytes) has been downloaded, and stored in {output_dir}")
        return

    def download_web(self,):
        try:
            # 发起HTTP GET请求
            response = requests.get(self.url, headers=self.headers, proxies=self.proxies)

            # 检查请求是否成功
            if response.status_code == 200:
                # 获取网页源码
                encoding = chardet.detect(response.content)['encoding']
                response.encoding = encoding
                html_content = response.text
                return html_content
            else:
                print(f"请求失败，状态码：{response.status_code}")
        except requests.exceptions.RequestException as e:
            print("请求发生异常：", str(e))

        return None

    def _get_item_by_text(self, father, text, res=None):
        if res is None:
            res = set()
        for child in father.children:
            if text in child.text:
                if type(child) is NavigableString:
                    res.add(child)
                    continue
                try:
                    if child.children is None or type(child.children) is NavigableString:
                        res.add(child)
                    else:
                        self._get_item_by_text(child, text, res)
                except Exception as e:
                    print(e)
                    res.add(child)
        return

    def _get_item_by_text_in_div(self, text):
        divs = self.bs.body.find_all("div")
        res = set()
        for div in divs:
            self._get_item_by_text(div, text, res)

        return res

    def _get_item_by_text_in_li(self, text):
        lis = self.bs.body.find_all("li")

        res = set()
        for li in lis:
            self._get_item_by_text(li, text, res)

        return res

    def get_item_by_text(self, text):
        res = self._get_item_by_text_in_li(text)
        if not res:
            res = self._get_item_by_text_in_div(text)

        res_lst = []
        for it in res:
            lst = []
            p = it.find_parent()
            while p:
                if p.name == "body":
                    break
                attr = ""
                if "id" in p.attrs:
                    attr = f"#{p.attrs['id']}"
                elif "class" in p.attrs and p.attrs["class"]:
                    attr = f".{p.attrs['class'][0]}"
                lst.append(f"{p.name}{attr}")
                p = p.find_parent()
            lst = lst[::-1]
            if len(lst) > 5:
                lst = lst[-5:]
            res_lst.append(" ".join(lst))
        return res_lst

    @staticmethod
    def get_related_links(item, depth=5):
        links = set()
        for _ in range(depth):
            try:
                for a in item.find_all("a"):
                    links.add(a["href"])
            except Exception as e:
                print(e)
                pass
            item = item.parent

        if links:
            print(format_string("related links"))
            for link in links:
                print(link)
        return links

    def get_item_by_href(self, href):
        lst = self.bs.find_all("a")
        for it in lst:
            if it["href"] == href:
                print(format_string("<a> attrs"))
                print(json.dumps(it.attrs, ensure_ascii=False, indent=4))
                return it

        return None

    def get_links_by_attr(self, **attr):
        lst = self.bs.find_all("a", **attr)
        links = []
        parsed_url = urlparse(self.url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        if lst:
            links = [base_url + it["href"] for it in lst]

        return links
