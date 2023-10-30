# encoding=utf-8
# created @2023/10/30
# created by zhanzq
#

import os
import requests
from bs4 import BeautifulSoup as BS


class WEB:
    def __init__(self, url, proxies=None):
        self.url = url
        self.proxies = proxies

    def download(self, output_dir):
        resp = requests.request("get", url=self.url, proxies=self.proxies)
        file_name = self.url.split("/")[-1]
        output_path = os.path.join(output_dir, file_name)
        with open(output_path, "wb") as writer:
            writer.write(resp.content)

        print(f"{file_name} has been downloaded, and stored in {output_dir}")
        return

    def parse(self):
        resp = requests.request("get", url=self.url, proxies=self.proxies)
        html = resp.content
        bs = BS(html)

        return bs

