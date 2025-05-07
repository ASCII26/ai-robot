from PIL import Image, ImageDraw

class Matrix:
    def __init__(self, draw=None, width=0, height=0):
        self._draw = draw
        self.width = width
        self.height = height
        self.img = None # when new(), create img,default is None
        self.matrix = [[0 for _ in range(width)] for _ in range(height)]
        
    def set_pixel(self, x, y, value):
        """设置指定位置的像素值"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.matrix[y][x] = value
            
    def get_pixel(self, x, y):
        """获取指定位置的像素值"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.matrix[y][x]
        return 0
        
    def clear(self):
        """清空矩阵"""
        self.matrix = [[0 for _ in range(self.width)] for _ in range(self.height)]
    
    def new(self):
        self.img = Image.new("1", (self.width, self.height), 0)
        self._draw = ImageDraw.Draw(self.img)
        return self._draw
        
    def draw(self, pos=(0,0),transparent=True):
        """绘制矩阵"""
        for y in range(self.height):
            for x in range(self.width):
                if self.matrix[y][x]:
                    self._draw.point((x + pos[0], y + pos[1]), fill=255)
                elif transparent == False:
                    self._draw.point((x + pos[0], y + pos[1]), fill=0)
                    
    def draw_pattern(self, pattern, x_offset=0, y_offset=0):
        """绘制预定义图案"""
        for y, row in enumerate(pattern):
            for x, value in enumerate(row):
                self.set_pixel(x + x_offset, y + y_offset, value)
                
    def get_matrix(self):
        """获取当前矩阵数据"""
        return self.matrix
        
    def set_matrix(self, matrix):
        """设置整个矩阵数据，并自动调整宽高"""
        if not matrix or not all(isinstance(row, list) for row in matrix):
            return
        self.height = len(matrix)
        self.width = len(matrix[0]) if self.height > 0 else 0
        self.matrix = matrix 