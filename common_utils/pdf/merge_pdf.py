# encoding=utf-8
# created @2023/9/12
# created by zhanzq
#

import os
from PyPDF2 import PdfMerger
from PIL import Image
import re


class PDF:
    def __init__(self, pdf_path):
        self.output_path = pdf_path

    def merge_pdf(self, input_dir):
        """
        合并input_dir下的所有pdf文件，按文件名称升序排序，非数字命名的文件忽略
        :param input_dir: 待合并文件所在目录
        :return:
        """
        pdf_lst = [f for f in os.listdir(input_dir) if re.fullmatch(pattern="\\d+.pdf", string=f)]
        pdf_lst.sort(key=lambda it: int(it.split(".")[0]))
        pdf_lst = [os.path.join(input_dir, filename) for filename in pdf_lst]
        file_merger = PdfMerger()
        for pdf in pdf_lst:
            file_merger.append(pdf)     # 合并pdf文件

        file_merger.write(self.output_path)

        return

    def merge_jpg(self, input_dir):
        """
        合并input_dir下的所有jpg文件，按文件名称升序排序
        :param input_dir: 待合并文件所在目录
        :return:
        """
        if not os.path.exists(input_dir):
            print(f"目录{input_dir}不存在")
            return

        jpg_files = os.listdir(input_dir)
        jpg_files.sort()
        # 创建 PDF 文件写入器
        image_lst = []
        for img_file in jpg_files:
            # 打开图片文件
            jpg_path = os.path.join(input_dir, img_file)
            image = Image.open(jpg_path)
            image = image.convert("RGB")
            image_lst.append(image)

        # 保存 PDF 文件
        image_lst[0].save(self.output_path, save_all=True, append_images=image_lst[1:])

        return


def main():

    return


if __name__ == "__main__":
    main()
