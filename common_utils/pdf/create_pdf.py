# encoding=utf-8
# created @2023/9/7
# created by zhanzq
#
import os

from fpdf import FPDF
from common_utils.pdf.color import COLOR

from common_utils.utils import gen_add_or_sub_questions


class PDF(FPDF):
    def __init__(self,
                 pdf_path,                  # pdf文件保存路径
                 font_dir=None,             # 中文字体库路径
                 unit="pt",                 # 默认单位为磅
                 # format="A4",               # 默认尺寸为A4
                 ):
        FPDF.__init__(self, unit=unit, format="A4")
        self.output_path = pdf_path
        self.font_dir = font_dir
        self.load_fonts()

    def load_fonts(self):
        if not self.font_dir:
            return

        font_files = os.listdir(self.font_dir)

        for font_file in font_files:
            if font_file.endswith("ttf"):
                font_name = font_file.split(".")[0]
                font_path = os.path.join(self.font_dir, font_file)
                try:
                    self.add_font(font_name, '', font_path, True)
                    self.fonts[font_name]["ttffile"] = font_path
                except Exception as e:
                    print(e)

        return

    def set_foot_color(self, color):
        pass

    def save(self):
        self.output(self.output_path)

    def draw_line(self, **kwargs):
        color = kwargs.get("color", (0, 0, 0))
        width = kwargs.get("width", 0.5)
        rect = kwargs.get("rect")
        dashed = kwargs.get("dashed", False)
        if rect is None:
            rect = kwargs.get("x1"), kwargs.get("y1"), kwargs.get("x2"), kwargs.get("y2")
        self.set_draw_color(*color)
        self.set_line_width(width)
        if dashed:
            x1, y1, x2, y2 = rect
            self.dashed_line(x1=x1, y1=y1, x2=x2, y2=y2, dash_length=3, space_length=3)
        else:
            self.line(*rect)
        return

    def draw_rect(self, **kwargs):
        color = kwargs.get("color", (0, 0, 0))
        width = kwargs.get("width", 0.5)
        rect = kwargs.get("rect")
        style = kwargs.get("style", "S")
        if rect is None:
            x1, y1, x2, y2 = kwargs.get("x1"), kwargs.get("y1"), kwargs.get("x2"), kwargs.get("y2")
        else:
            x1, y1, x2, y2 = rect[0], rect[1], rect[2], rect[3]
        self.set_draw_color(*color)
        self.set_line_width(width)

        self.rect(x=x1, y=y1, w=x2-x1, h=y2-y1, style=style)
        return

    def draw_char_cell(self, x0, y0, cell_size=41, color=(0, 150, 0)):
        """
        :param x0: left top x
        :param y0: left top y
        :param cell_size: char cell size, default 41
        :param color: pinyin cell line color, default dark green
        """
        x = x0 + cell_size / 2
        y = y0 + cell_size / 2
        self.draw_rect(x1=x0, y1=y0, x2=x0 + cell_size, y2=y0 + cell_size, width=1, color=color)
        self.draw_line(x1=x0, y1=y, x2=x0 + cell_size, y2=y, dashed=True, color=color)
        self.draw_line(x1=x, y1=y0, x2=x, y2=y0 + cell_size, dashed=True, color=color)

        return

    def draw_pinyin_cell(self, x0, y0, height=18, width=41, color=(0, 150, 0)):
        """
        :param x0: left bottom x
        :param y0: left bottom y
        :param height: pinyin cell height, default 18
        :param width: pinyin cell width, default 41
        :param color: pinyin cell line color, default dark green
        """
        delta_h = height / 3
        _y1, _y2, _y3 = y0 - 3 * delta_h, y0 - 2 * delta_h, y0 - delta_h
        x1, x2 = x0, x0 + width
        self.draw_line(x1=x1, y1=_y1, x2=x2, y2=_y1, width=0.5, color=color)
        self.draw_line(x1=x1, y1=_y2, x2=x2, y2=_y2, width=0.25, color=color, dashed=True)
        self.draw_line(x1=x1, y1=_y3, x2=x2, y2=_y3, width=0.25, color=color, dashed=True)

        return

    def draw_char_pinyin_page(self, x0=46, y0=106, char_cell_size=41, pinyin_height=18, row_num=8, col_num=12):
        row_y0 = y0
        delta_height = 21
        for row_idx in range(row_num):
            row_x0 = x0
            for cell_idx in range(col_num):
                self.draw_char_cell(x0=row_x0, y0=row_y0, cell_size=char_cell_size)
                self.draw_pinyin_cell(x0=row_x0, y0=row_y0, height=pinyin_height, width=char_cell_size)
                row_x0 += char_cell_size

            row_y0 += char_cell_size + pinyin_height + delta_height

        return

    def _set_text_color(self, color: str):
        self.set_text_color(**COLOR.rgb(color))

    def _set_draw_color(self, color: str):
        self.set_draw_color(**COLOR.rgb(color))

    def add_content(self, text_info):
        """
        写入正文内容到pdf文档
        :param text_info: 待写入的文本信息，包含text, pos, font, color, size等字段
        :return:
        输入示例：
        {
            'text': '初',
            'pinyin': 'chū',
            'pos': (215.25155639648438, 104.67916870117188, 245.7286834716797, 147.34715270996094),
            'font': 'STKaitiSC-Regular',
            'color': (135, 135, 135),
            'size': 30.477128982543945
        }
        """
        pinyin = text_info.get("pinyin", "")
        text = text_info.get("text", "")
        font_name = text_info.get("font", "华文楷体")
        font_size = text_info.get("size", 41)
        text_color = text_info.get("color", (135, 135, 135))
        x1, y1, x2, y2 = text_info.get("pos", (0, 0, 0, 0))
        # bias_font = 0.835   # 华文楷体字体位置偏差
        # y2 *= bias_font
        self.set_font(font_name, '', font_size)
        try:
            self.set_text_color(*text_color)
            if text:
                self.set_font_size(font_size)
                self.set_xy(x=x1-2, y=y1)
                self.cell(w=font_size, h=font_size, txt=text, border=0, ln=0, align='C')

            # self.set_font(family="arial", style="", size=14)
            # self.text(x1-2, y2-8, text)
            # shift = (5 - len(pinyin)) * 6
            # self.text(x1+shift, y1-6, pinyin)
            if pinyin:
                self.set_font_size(16)
                self.set_xy(x=x1, y=y1-31)
                self.cell(w=font_size, h=font_size, txt=pinyin, border=0, ln=0, align='C')
        except Exception as e:
            print(e)
            pass

        return


class MathQuestionPDF(PDF):
    def __int__(self,
                pdf_path,
                max_lines_per_page=15,              # pdf页面最大行数
                footer_info="小学数学——10以内的加法",  # 页脚信息
                header_info="小学数学",              # 页眉信息
                ):
        super().__init__(pdf_path=pdf_path, unit="mm")
        self.footer_info = footer_info
        self.header_info = header_info
        self.max_lines_per_page = max_lines_per_page

    def header(self):
        # Logo
        self.image('/Users/zhanzq/Downloads/math.jpg', x=10, y=8, w=33, h=25)
        # Arial bold 15
        self.set_font('Times', size=15)
        # Move to the right
        self.cell(80)
        self._set_text_color("blue")
        # Title
        self.cell(30, 10, self.header_info, 0, 0, 'C')
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
        self.cell(0, 10, self.footer_info, 0, 0, 'C')
        self._set_text_color("black")
        self._set_draw_color("blue")
        self.line(50, 20, 195, 20)

        return

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
                print(e)
                pass

        return


def main():

    return


if __name__ == "__main__":
    main()
