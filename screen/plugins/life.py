import random
from screen.base import DisplayPlugin
from until.input import ecodes

GAME_FRAME_TIME = 1 / 30

class LifeDisplay(DisplayPlugin):
    def __init__(self, manager, width, height):
        self.name = "life"
        super().__init__(manager, width, height)
        self.cell_size = 2
        self.grid_width = self.width // self.cell_size
        self.grid_height = self.height // self.cell_size
        self.grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.initialize_grid()
        
    def initialize_grid(self):
        # 随机初始化网格
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                self.grid[y][x] = random.randint(0, 1)
                
    def count_neighbors(self, x, y):
        count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.grid_width
                ny = (y + dy) % self.grid_height
                count += self.grid[ny][nx]
        return count
    
    def update(self):
        # 清空画布
        self.clear()
        
        # 更新网格状态
        new_grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                neighbors = self.count_neighbors(x, y)
                if self.grid[y][x] == 1:
                    if neighbors < 2 or neighbors > 3:
                        new_grid[y][x] = 0
                    else:
                        new_grid[y][x] = 1
                else:
                    if neighbors == 3:
                        new_grid[y][x] = 1
        self.grid = new_grid
        
        # 绘制当前状态
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.grid[y][x] == 1:
                    self.draw.rectangle([
                        x * self.cell_size,
                        y * self.cell_size,
                        (x + 1) * self.cell_size - 1,
                        (y + 1) * self.cell_size - 1
                    ], fill=1)
        
    def get_frame_time(self):
        return GAME_FRAME_TIME
    
    def set_active(self, active):
        super().set_active(active)
        if active:
            self.initialize_grid()
            self.manager.key_listener.on(self.key_callback)
        else:
            self.manager.key_listener.off(self.key_callback)
    
    def key_callback(self, device_name, evt):
        if evt.value == 1:  # key down
            if evt.code == ecodes.KEY_KP1 or evt.code == ecodes.KEY_KP2:
                self.initialize_grid()
