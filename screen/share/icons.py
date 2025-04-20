from PIL import Image, ImageDraw

class Icons:
    size=6 #icon size
    
    @staticmethod
    def speaker(x=0, y=0, size=size):
        """draw speaker icon"""
        points = [
            (x+3, y+3),  # 左上
            (x+6, y+1),  # 右上
            (x+6, y+6),  # 右下
            (x+3, y+4),  # 左下
        ]

        return points
    
    @staticmethod
    def volume_wave(x=0, y=0, level=0.5):
        """draw volume wave
        level: 0.0-1.0 volume level
        """
        waves = []
        if level > 0.0:  # 第一道音波
            waves.append((x+9, y+3, x+9, y+4))
        if level > 0.3:  # 第二道音波
            waves.append((x+11, y+2, x+11, y+5))
        if level > 0.6:  # 第三道音波
            waves.append((x+13, y+1, x+13, y+6))
        return waves
    
    @staticmethod
    def play(x=0, y=0, size=size):
        """draw play icon"""
        points = [
            (x+1, y+1),  # 左上
            (x+size-3, y+3),  # 右上
            (x+size-3, y+3),  # 右下
            (x+1, y+size-1),  # 左下
        ]
        return points
    
    @staticmethod
    def pause(x=0, y=0, size=size):
        """draw pause icon"""
        bars = [
            (x+1, y+1, x+1, y+size-1),  # 左竖条
            (x+3, y+1, x+3, y+size-1),  # 右竖条
        ]
        return bars
    
    @staticmethod
    def airplay(x=0, y=0, size=size):
        """draw airplay icon
        size: icon size
        """
        # 绘制三角形
        triangle = [
            (x+2, y+size),  # 左下
            (x+3, y+size-1),  # 顶部
            (x+4, y+size-1),  # 右下
            (x+5, y+size),  # 左下
        ]
        
        # 绘制波浪线，每个波浪线有不同的角度范围
        waves = [
            # (bounding_box, start_angle, end_angle)
            ((x+1, y+size-4, x+size, y+size+2), 200, 340),  # 第一道波浪，较平缓
            ((x-1, y+size-6, x+size+2, y+size+4), 210, 330),  # 第二道波浪，更弯曲
        ]
        
        return triangle, waves
    
class IconDrawer:
    def __init__(self, draw):
        self.draw = draw
    
    def draw_airplay(self, x=0, y=0):
        """draw airplay icon"""
        triangle, waves = Icons.airplay(x, y)
        self.draw.polygon(triangle, fill=255)
        for wave_box, start_angle, end_angle in waves:
            self.draw.arc(wave_box, start=start_angle, end=end_angle, fill=255)
    
    def draw_play(self, x=0, y=0):
        """draw play icon"""
        points = Icons.play(x, y)
        self.draw.polygon(points, fill=255)
    
    def draw_pause(self, x=0, y=0):
        """draw pause icon"""
        bars = Icons.pause(x, y)
        for bar in bars:
            self.draw.rectangle(bar, fill=255)

    def draw_volume_wave(self, level, x=110, y=0):
        """draw volume wave"""
        points = Icons.speaker(x, y)
        self.draw.polygon(points, fill=255)
        waves = Icons.volume_wave(x, y, level)

        for wave in waves:
            self.draw.line(wave, fill=255)
