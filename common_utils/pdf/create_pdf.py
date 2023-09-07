# encoding=utf-8
# created @2023/9/7
# created by zhanzq
#

from fpdf import FPDF

from common_utils.utils import gen_add_or_sub_questions


class PDF(FPDF):

    def header(self):
        # Logo
        self.image('/Users/zhanzq/Downloads/math.jpg', 10, 8, 33)
        # Arial bold 15
        self.add_font('华文楷体', '', './fonts/华文楷体.ttf', True)
        self.set_font('华文楷体', size=15)
        # Move to the right
        self.cell(80)
        self.set_text_color(r=0, g=0, b=255)
        # Title
        self.cell(30, 10, '小学数学', 0, 0, 'C')
        self.set_text_color(r=0, g=0, b=0)
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
        self.set_text_color(r=0, g=0, b=255)

        # Page number
        self.cell(0, 10, '小学数学 —— 10以内的加法', 0, 0, 'C')
        self.set_text_color(r=0, g=0, b=0)
        self.set_draw_color(r=0, g=0, b=255)
        self.line(50, 20, 195, 20)

        return

    def add_appendix_info(self, appendix_info=("姓名：", "日期：", "得分："), text_color={"r": 0, "g": 0, "b": 255}):
        """
        在页面最下面添加附加信息，如"日期"等
        :param appendix_info: tuple, 各种附加信息
        :param text_color: 文本颜色，默认为蓝色
        :return:
        """
        self.set_draw_color(**text_color)
        self.set_text_color(**text_color)
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
        self.set_text_color(r=0, g=0, b=0)

        return

    def print_content(self, lines, max_lines_per_page=15, column=3):
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
    pdf = PDF()
    pdf.print_content(lines=add_lst[:25], column=2)
    pdf.output('test.pdf', 'F')


if __name__ == "__main__":
    main()
