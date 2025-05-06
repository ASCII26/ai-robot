from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import time
from until.animation import Animation
from until.matrix import Matrix

# 绘制一个简单的图案
ARROW_PATTERN = [
    [0, 0, 1],
    [0, 1, 0],
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1]
]

        
class TextArea:
    def __init__(self, width=64, height=32, font = None,line_spacing=2):
        self.width = width
        self.height = height
        
        # 加载默认字体
        if font is None:
            font_path = os.path.join(os.path.dirname(__file__), 'FusionPixel.ttf')
            self.font = ImageFont.truetype(font_path, 8)  # 使用8px字体
        else:
            self.font = font
            
        self.text_boxes = []  # 存储所有文本盒子   
        self.line_height = 8  # 字体默认高度
        self.line_spacing = line_spacing  # 行间距
        self.total_line_height = self.line_height + self.line_spacing  # 总行高

        self.left_padding = 3
        self.max_render_boxes = 5  # 最大可见文本盒子数量，控制同时渲染的文字数量
        self.last_text_box = None
        self.temp_img = None
        self.viewport_height = 0
        
        self.scroll_offset = 0  # 滚动偏移量
        
        self.ani = Animation()
        self.ani.reset("scroll")
        
    def append_text(self, text):
        """添加新文本，自动换行并滚动"""
        # 将文本按宽度换行，每个中文字符占8像素
        wrapped_lines = textwrap.wrap(text, width= (self.width - self.left_padding) // 8)  # 假设每个字符宽度为8像素
        
        # 创建新的文本盒子
        self.last_text_box = {
            'lines': wrapped_lines,
            'height': len(wrapped_lines) * self.total_line_height
        }
        
        # 更新滚动位置
        self._update_scroll()
        self.temp_img = None
        # 添加到文本盒子列表
        self.text_boxes.append(self.last_text_box)       
        
    def _update_scroll(self):
        """更新滚动位置"""
        # 计算最后几个文本盒子的总高度
        if len(self.text_boxes) >= self.max_render_boxes:
            visible_boxes = self.text_boxes[-self.max_render_boxes+1:]
        else:
            visible_boxes = self.text_boxes[-self.max_render_boxes:]
            
        total_height = sum(box['height'] for box in visible_boxes)
        
        # 如果内容超出显示区域，需要滚动
        if total_height > self.height:
            self.scroll_offset = total_height - self.height
        else:
            self.scroll_offset = 0
                        
    def render(self):
        """渲染当前显示区域"""
        # 创建新的图像
        
        if self.temp_img is None:
            visible_boxes = self.text_boxes[-self.max_render_boxes:]
            total_height = sum(box['height'] for box in visible_boxes)

            self.temp_img = Image.new('1', (self.width-self.left_padding, total_height), 0)
            draw = ImageDraw.Draw(self.temp_img)
            
            # 当前绘制位置
            y = -self.scroll_offset
            
            # 只遍历最后几个文本盒子
            for box in visible_boxes:
                # 绘制每一行
                for line in box['lines']:
                    # 如果行在当前可见区域内或刚好在可视区外一行
                    draw.text((self.left_padding, y), line, font=self.font, fill=255)
                    y += self.total_line_height
                    
            if self.last_text_box is not None:
                self.viewport_height = y
                                
                if self.viewport_height > self.height:
                    self.ani.reset("scroll")
        
        
        img = Image.new('1', (self.width, self.height), 0)
        draw = ImageDraw.Draw(img)
        
        target = self.viewport_height-self.height-self.line_spacing
        
        bottom_offset = max(0,int(self.ani.run("scroll",target)))
        img.paste(self.temp_img, (self.left_padding-1,0 - bottom_offset))
        draw.line((2,1,2,self.height-1),fill=255)
        
        # 绘制三角形
        matrix = Matrix(draw)
        matrix.set_matrix(ARROW_PATTERN)
        matrix.draw((0, 8),transparent=False)
        return img


    def clear(self):
        """清空所有文本"""
        self.text_boxes = []
        self.scroll_offset = 0