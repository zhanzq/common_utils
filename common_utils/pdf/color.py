# encoding=utf-8
# created @2023/9/8
# created by zhanzq
#

class Color:
    def __init__(self):
        self.rgb_colors = dict()
        self._construct_common_color()

    def _construct_rgb_color(self, name, r, g, b):
        self.rgb_colors[name] = {
            "r": r,
            "g": g,
            "b": b
        }

    def _construct_common_color(self):
        self._construct_rgb_color("red", 255, 0, 0)
        self._construct_rgb_color("green", 0, 255, 0)
        self._construct_rgb_color("blue", 0, 0, 255)
        self._construct_rgb_color("black", 0, 0, 0)
        self._construct_rgb_color("white", 255, 255, 255)

    def rgb(self, name):
        if name not in self.rgb_colors:
            name = "black"
        return self.rgb_colors.get(name)


COLOR = Color()


def main():
    red = COLOR.rgb("red")
    print(red)


if __name__ == "__main__":
    main()
