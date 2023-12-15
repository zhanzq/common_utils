# encoding=utf-8
# created @2023/12/15
# created by zhanzq
#

from common_utils.text_io.word import Docx


class Poetry(Docx):
    def __init__(self, path):
        super().__init__(path)

    def add_poetry_title(self, title):
        paragraph = self.doc.add_paragraph()
        run = paragraph.add_run(title)
        paragraph.alignment = 1
        self.set_font(run, size='小一', name='华文楷体')

        return

    def add_poetry_author(self, author):
        paragraph = self.doc.add_paragraph()
        paragraph.alignment = 2
        run = paragraph.add_run(author)
        self.set_font(run, size=20, name='华文楷体')

        return

    def add_poetry_content(self, content):
        paragraph = self.doc.add_paragraph()
        run = paragraph.add_run(content)
        paragraph.alignment = 1
        self.set_font(run, size=20, name='华文楷体')

        return

    def add_poetry_date(self, date):
        paragraph = self.doc.add_paragraph()
        run = paragraph.add_run(date)
        paragraph.alignment = 2
        self.set_font(run, size='小二', name='华文楷体')

        return

    def add_poetry(self, poetry_info):
        self.add_poetry_title(poetry_info.get("title"))
        self.add_poetry_author(poetry_info.get("author"))
        self.add_poetry_content(poetry_info.get("content"))
        self.add_poetry_date("")

        return


if __name__ == "__main__":
    poetry_item = Poetry(path="/Users/zhanzq/Downloads/古诗测试.docx")
    poetry_item.add_poetry_title(title="梅花")
    poetry_item.save()
