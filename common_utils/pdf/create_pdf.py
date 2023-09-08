# encoding=utf-8
# created @2023/9/7
# created by zhanzq
#
import os

from fpdf import FPDF
from color import COLOR

from common_utils.utils import gen_add_or_sub_questions


class PDF(FPDF):
    def __init__(self,
                 output_path,               # pdf文件保存路径
                 max_lines_per_page=15,     # pdf页面最大行数
                 footer_info="",            # 页脚信息
                 header_info=""             # 页眉信息
                 ):
        FPDF.__init__(self)
        self.output_path = output_path
        self.load_fonts()

    def load_fonts(self, font_dir="./fonts"):
        font_files = os.listdir(font_dir)

        for font_file in font_files:
            if font_file.endswith("ttf"):
                font_name = font_file.split(".")[0]
                font_path = os.path.join(font_dir, font_file)
                try:
                    self.add_font(font_name, '', font_path, True)
                except Exception as e:
                    print(e)

        return

    def set_foot_color(self, color):
        pass

    def save(self):
        self.output(self.output_path)

    def header(self):
        # Logo
        self.image('/Users/zhanzq/Downloads/math.jpg', x=10, y=8, w=33, h=25)
        # Arial bold 15
        self.set_font('华文楷体', size=15)
        # Move to the right
        self.cell(80)
        self._set_text_color("blue")
        # Title
        self.cell(30, 10, '小学数学', 0, 0, 'C')
        self._set_text_color("black")
        # Line break
        self.ln(25)

        return

    # Page footer
    def footer(self):
        self.add_appendix_info(appendix_info=("姓名：", "日期：", "得分："))
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('华文楷体', size=15)
        self._set_text_color("blue")

        # Page number
        self.cell(0, 10, '小学数学 —— 10以内的加法', 0, 0, 'C')
        self._set_text_color("black")
        self._set_draw_color("blue")
        self.line(50, 20, 195, 20)

        return

    def _set_text_color(self, color: str):
        self.set_text_color(**COLOR.rgb(color))

    def _set_draw_color(self, color: str):
        self.set_draw_color(**COLOR.rgb(color))

    def add_appendix_info(self, appendix_info=("姓名：", "日期：", "得分："), text_color='blue'):
        """
        在页面最下面添加附加信息，如"日期"等
        :param appendix_info: tuple, 各种附加信息
        :param text_color: 文本颜色，默认为蓝色
        :return:
        """
        self._set_draw_color(text_color)
        self._set_text_color(text_color)
        self.set_font('华文楷体', size=18)
        left, right, bottom = 10, 195, 265
        self.line(left, bottom, right, bottom)
        self.set_y(bottom)
        width_column = 210//len(appendix_info)
        for item in appendix_info:
            self.cell(w=width_column, h=10, txt=item, ln=0)
        self.ln()   # 换行
        y = self.get_y()
        self.line(left, y, right, y)
        # 恢复字体颜色
        self._set_text_color("black")

        return

    def add_content(self, lines, max_lines_per_page=15, column=3):
        """
        写入正文内容到pdf文档
        :param lines: 待写入的内容
        :param max_lines_per_page: 每页最多写入的行数，最大为15行，默认为15行
        :param column: 每页写入的列数，默认为3列
        :return:
        """

        column_width = 210 // column
        self.set_font('Times', '', 18)
        cur_lines = 0
        for i in range(0, len(lines), column):
            try:
                if cur_lines % max_lines_per_page == 0:
                    self.add_page()
                for column_idx in range(column):
                    self.cell(w=column_width, h=15, txt=lines[i + column_idx], border=0, ln=0, align='L')
                self.ln()
                cur_lines += 1
            except Exception as e:
                pass

        return


def main():
    add_lst, sub_lst, mix_lst = gen_add_or_sub_questions(10)
    # Instantiation of inherited class
    pdf = PDF(output_path="test.pdf")
    pdf.add_content(lines=add_lst[:25], column=2)
    pdf.save()


if __name__ == "__main__":
    main()
