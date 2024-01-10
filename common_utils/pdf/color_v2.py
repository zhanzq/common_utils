# encoding=utf-8
# created @2023/12/27
# created by zhanzq
#

from enum import Enum


class Color(Enum):
    BLACK = ('黑色', (0, 0, 0))
    RED = ('红色', (255, 0, 0))
    GREEN = ('绿色', (0, 255, 0))
    BLUE = ('蓝色', (0, 0, 255))
    YELLOW = ('黄色', (255, 255, 0))
    CYAN = ('青色', (0, 255, 255))
    GRAY = ('灰色', (192, 192, 192))
    WHITE = ('白色', (255, 255, 255))
    IVORY_BLACK = ('象牙黑', (88, 87, 86))
    SKY_GRAY = ('天蓝灰', (202, 235, 216))
    COOL_GRAY = ('冷灰', (128, 138, 135))
    WARM_GRAY = ('暖灰', (128, 118, 105))
    IVORY_GRAY = ('象牙灰', (251, 255, 242))
    SLATE_GRAY = ('石板灰', (118, 128, 105))
    LINEN_GRAY = ('亚麻灰', (250, 240, 230))
    SMOKE_GRAY = ('白烟灰', (245, 245, 245))
    ALMOND_GRAY = ('杏仁灰', (255, 235, 205))
    EGGSHELL_GRAY = ('蛋壳灰', (252, 230, 202))
    SEASHELL_GRAY = ('贝壳灰', (255, 245, 238))
    CADMIUM_RED = ('镉红', (227, 23, 13))
    CADMIUM_YELLOW = ('镉黄', (255, 153, 18))
    BRICK_RED = ('砖红', (156, 102, 31))
    BANANA_YELLOW = ('香蕉黄', (227, 207, 87))
    CORAL_RED = ('珊瑚红', (255, 127, 80))
    GOLD_YELLOW = ('金黄', (255, 215, 0))
    TOMATO_RED = ('番茄红', (255, 99, 71))
    FLESH_YELLOW = ('肉黄', (255, 125, 64))
    PINK = ('粉红', (255, 192, 203))
    PALE_YELLOW = ('粉黄', (255, 227, 132))
    INDIAN_RED = ('印度红', (176, 23, 31))
    ORANGE_YELLOW = ('橘黄', (255, 128, 0))
    DEEP_RED = ('深红', (255, 0, 255))
    RADISH_YELLOW = ('萝卜黄', (237, 145, 33))
    MAROON = ('黑红', (116, 0, 0))
    DARK_YELLOW = ('黑黄', (85, 102, 0))
    BROWN = ('棕色', (128, 42, 42))
    EARTH_COLOR = ('土色', (199, 97, 20))
    CHARTREUSE = ('黄绿色', (127, 255, 0))
    TAN = ('沙棕色', (244, 164, 95))
    TEAL = ('青绿色', (64, 224, 205))
    BROWNISH = ('棕褐色', (210, 180, 140))
    INDIGO = ('靛青色', (8, 46, 84))
    ROSE_RED = ('玫瑰红', (188, 143, 143))
    FOREST_GREEN = ('森林绿', (34, 139, 34))
    AUBURN = ('赫色', (160, 82, 45))
    GRASS_GREEN = ('草绿色', (107, 142, 35))
    SIENNA = ('肖贡土色', (199, 97, 20))
    MANGANESE_BLUE = ('锰蓝', (3, 168, 158))
    LAVENDER = ('淡紫色', (218, 112, 214))
    DARK_BLUE = ('深蓝', (25, 25, 112))
    VIOLET = ('紫罗兰', (138, 43, 226))
    TURQUOISE_BLUE = ('土耳其蓝', (0, 199, 140))
    PURPLE = ('胡紫色', (153, 51, 250))

    def __init__(self, name, rgb):
        self._name = name
        self._rgb = rgb

    @property
    def name(self):
        return self._name

    @property
    def rgb(self):
        return self._rgb


if __name__ == "__main__":
    print(Color.RED.name)
    print(Color.RED.rgb)
    print(Color.白.rgb)
