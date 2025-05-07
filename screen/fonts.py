from PIL import ImageFont

class Fonts:
    def __init__(self):
        self.size_5 = ImageFont.truetype("./fonts/QuinqueFive.ttf", 5)
        self.size_8 = ImageFont.truetype("./fonts/fusion-pixel-8px.ttf", 8)
        self.size_10 = ImageFont.truetype("./fonts/fusion-pixel-10px.ttf", 10)
        self.size_12 = ImageFont.truetype("./fonts/fusion-pixel-12px.ttf", 12)
        self.size_16 = ImageFont.truetype("./fonts/fusion-pixel-8px.ttf", 16)