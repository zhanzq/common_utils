# encoding=utf-8
# created @2023/11/8
# created by zhanzq
#

import re
import fitz


class PDF:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.content = []

    @staticmethod
    def remove_references(text):
        # format 1: [DCLT19]
        text = re.sub(pattern=r"\[[a-zA-Z0-9, +]+\]", repl="", string=text)

        return text

    @staticmethod
    def remove_redundant_spaces(text):
        text = text.replace("  ", " ").replace(" .", ".").replace(" ,", ",").replace("- ", "-")

        return text

    def _extract_page_content(self, page):
        left, top, right, bottom = self.get_page_bound(page)
        blocks = page.get_text_blocks()
        #     print(f"left: {left}, bottom:  {bottom}")
        content = []
        for block in blocks:
            x0, y0, x1, y1, text, row, col = block

            text = text.replace("\n", " ")
            text = self.remove_references(text)
            text = self.remove_redundant_spaces(text)

            if x1 < left or y1 > bottom:
                print(f"ignored text: {text}")
                continue
            else:
                content.append(text)

        return "\n".join(content)

    @staticmethod
    def _get_bottom(page):
        lst = page.get_drawings()

        bottom = page.bound()[3] - 50
        for it in lst:
            x0, y0, x1, y1 = it["rect"]
            if abs(y0 - y1) <= 0.01:
                if bottom - y0 >= 90 or it["width"] > 0.4:
                    continue
                else:
                    bottom = y0
                    break

        return bottom

    @staticmethod
    def _get_left(page):
        lst = []
        blocks = page.get_text_blocks()
        for block in blocks:
            x0, y0, x1, y1, text, row, col = block
            lst.append(int(x0))

        lst.sort()
        left = 0
        for i in range(len(lst) - 1):
            if lst[i] == lst[i + 1]:
                left = lst[i]
                break

        return left

    def get_page_bound(self, page):
        _, top, right, _ = page.bound()
        left = self._get_left(page)
        bottom = self._get_bottom(page)

        return left, top, right, bottom

    def extract_content(self):
        for page in self.doc.pages():
            page_content = self._extract_page_content(page)
            self.content.extend(page_content)

        return

    def save_content(self, output_path):
        if not self.content:
            self.extract_content()

        with open(output_path, "w") as writer:
            writer.writelines(self.content)

        return
