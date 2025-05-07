from PIL import Image, ImageDraw
import random
import time
import math
from ui.animation import Animation
from ui.matrix import Matrix

from .emotion_pattern import PATTERN

WIDTH, HEIGHT = 80, 32  # 修改宽度为80
LOOK_DURATION = 2  # 每个位置停留2秒

EMOTIONS = {
            "neutral": {"left_eye": "open", "right_eye": "open","mask_rotation": [10,15]},
            "happy": {"left_eye": "laughing", "right_eye": "laughing"},
            "laughing": {"left_eye": "laughing", "right_eye": "laughing","shake":True},
            "funny": {"left_eye": "happy", "right_eye": "happy"},
            "sad": {"left_eye": "furrowed","right_eye": "furrowed","mask_rotation": [-30,-30]},
            "angry": {"left_eye": "furrowed", "right_eye": "furrowed","mask_rotation": [30,30],"shocked":True},
            "crying": {"left_eye": "furrowed", "right_eye": "furrowed","mask_rotation": [-30,-30],"breathe":True},
            "loving": {"left_eye": "hearts", "right_eye": "hearts"},
            "embarrassed": {"left_eye": "wide", "right_eye": "wide","shocked":True},
            "surprised": {"left_eye": "open", "right_eye": "wide","shocked":True},
            "shocked": {"left_eye": "wide", "right_eye": "wide","shocked":True},
            "thinking": {"left_eye": "open", "right_eye": "furrowed","mask_rotation": [0,20],"breathe":True},
            "winking": {"left_eye": "open", "right_eye": "winking"},
            "cool": {"left_eye": "furrowed", "right_eye": "furrowed","mask_rotation": [10,10]},
            "relaxed": {"left_eye": "relaxed", "right_eye": "relaxed","breathe":True},
            "delicious": {"left_eye": "winking", "right_eye": "winking"},
            "kissy": {"left_eye": "relaxed", "right_eye": "hearts"},
            "confident": {"left_eye": "nearly-close", "right_eye": "half-close"},
            "sleepy": {"left_eye": "sleeping", "right_eye": "sleeping","breathe":True},
            "silly": {"left_eye": "laughing", "right_eye": "open"},
            "confused": {"left_eye": "close", "right_eye": "close"},
            "listening": {"left_eye": "open", "right_eye": "winking","breathe":True},
        }
NO_BLINK = ["listening","sleepy", "confused","laughing","funny","relaxed","delicious"]

BLINK_INTERVAL = 2
BLINK_MAX_INTERVAL = 8
LOOK_AROUND_INTERVAL = 5
LOOK_AROUND_MAX_INTERVAL = 10
LOOK_AROUND_DURATION = 2
FURROWED_INTERVAL = 5
FURROWED_MAX_INTERVAL = 10
ANIMATION_DURATION = 0.2

# 绘制旋转的矩形
def _draw_rotated_rectangle(draw, x1, y1, x2, y2, angle, fill=0):
    """绘制旋转的矩形
    angle: 旋转角度（度）
    """
    # 计算矩形的中心点
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    
    # 矩形的四个顶点
    points = [
        (x1, y1),
        (x2, y1),
        (x2, y2),
        (x1, y2)
    ]
    
    # 旋转每个顶点
    rad = math.radians(angle)
    cos_val = math.cos(rad)
    sin_val = math.sin(rad)
    
    rotated_points = []
    for x, y in points:
        # 将点移动到原点
        dx = x - center_x
        dy = y - center_y
        
        # 旋转
        new_x = dx * cos_val - dy * sin_val
        new_y = dx * sin_val + dy * cos_val
        
        # 移回原位置
        rotated_points.append((new_x + center_x, new_y + center_y))
    
    # 绘制旋转后的矩形
    draw.polygon(rotated_points, fill=fill)

# 机器人表情类
class RobotEmotion:
    def __init__(self):
        # 初始化各个部分的动画状态
        self.left_eye_state = "open"
        self.right_eye_state = "open"
        self.mask_rotation = [0,0]
        
        # 初始化动画计时器
        self.last_blink_time = time.time()
        self.blink_interval = random.uniform(BLINK_INTERVAL, BLINK_MAX_INTERVAL)
        self.last_look_around_time = time.time()
        self.look_around_interval = random.uniform(LOOK_AROUND_INTERVAL, LOOK_AROUND_MAX_INTERVAL)
        self.last_furrowed_time = time.time()
        self.furrowed_interval = random.uniform(FURROWED_INTERVAL, FURROWED_MAX_INTERVAL)
        
        # 眼睛位置偏移
        self.target_offset_x = 0
        self.target_offset_y = 0

        
        self.anim = Animation(ANIMATION_DURATION)
        self.anim.reset("eye_position_x")
        self.anim.reset("eye_position_y")
        self.animation_duration = ANIMATION_DURATION  # 动画持续时间（秒）
        
        # 当前表情状态
        self.current_emotion = ""
        self.base_emotion = {}
        
        # 动画队列
        self.animation_queues = {}
        self.is_looking_around = False
        self.is_furrowed = False
        
        self.set_emotion("neutral")

    # 绘制眼睛
    def draw_eye(self, draw, state, mask_rotation):
        """绘制眼睛，根据不同的状态"""
        # 在20x20的画布上绘制眼睛
        eye_size = 16
        padding = 2  # 左右各留2像素的边距
        
        # 计算眼睛在20x20画布中的位置
        x1 = padding
        y1 = padding
        x2 = x1 + eye_size
        y2 = y1 + eye_size
        
        if state == "open":
            # 基础眼睛为圆形
            draw.ellipse((x1, y1, x2, y2), fill=255)
        elif state == "half-close":
            # 半闭眼为半圆
            draw.ellipse((x1, y1+4, x2, y2-4), fill=255)
        elif state == "nearly-close":
            # 半闭眼为半圆
            draw.ellipse((x1, y1+6, x2, y2-6), fill=255)
        elif state == "close":
            # 闭眼为一条线
            draw.line((x1+1, y1+8, x2-1, y1+8), fill=255, width=2)
        elif state == "laughing":
            offset = 3
            # 开心时向上弯曲的眼睛
            draw.ellipse((x1, y1+offset, x2, y2+offset), fill=255)
            draw.ellipse((x1-1, y1+offset+4, x2+1, y2+offset+4), fill=0) #mask
        elif state == "relaxed":
            offset = -3
            # 开心时向上弯曲的眼睛
            draw.ellipse((x1, y1+offset, x2, y2+offset), fill=255)
            draw.ellipse((x1-1, y1+offset-2, x2+1, y2+offset-2), fill=0) #mask
        elif state == "winking":
            offset = 2
            # 眨眼时向上弯曲的眼睛
            draw.ellipse((x1, y1+offset+4, x2, y2+offset-4), fill=255)
            draw.ellipse((x1, y1+offset+6, x2, y2+offset-2), fill=0)#mask
        elif state == "sleeping":
            offset = 2
            # 眨眼时向上弯曲的眼睛
            draw.ellipse((x1, y1+offset+4, x2, y2+offset-4), fill=255)
            draw.ellipse((x1, y1+offset+2, x2, y2+offset-6), fill=0)#mask
        elif state == "happy":
            # 开心时向上弯曲的眼睛
            draw.ellipse((x1, y1, x2, y2), fill=255)
            draw.ellipse((x1, y1+7, x2, y2), fill=0)#mask
        elif state == "furrowed":
            # 生气时向下弯曲的眼睛
            draw.ellipse((x1, y1, x2, y2), fill=255)
            # 根据旋转角度计算位移
            rad = math.radians(mask_rotation)
            # 计算旋转中心点到圆边缘的距离
            radius = eye_size / 2
            # 计算位移量，使用正弦函数使位移随角度变化
            offset = radius * math.sin(rad)
            # 根据旋转方向决定位移方向
            _draw_rotated_rectangle(draw, x1+offset, y1, x2+offset, y1+6, mask_rotation, fill=0)
      
        elif state == "wide":
            # 睁大的眼睛，画一个更大的
            draw.ellipse((x1-2, y1-2, x2+2, y2+2), fill=255)
        elif state == "hearts":
            # 绘制爱心
            matrix = Matrix(draw)
            matrix.set_matrix(PATTERN.HEARTS)
            matrix.draw((x1, y1))
            
    # 绘制表情
    def make_face(self):
        img = Image.new("1", (WIDTH, HEIGHT), 0)
        # 处理眼睛位置动画
        eye_offset_x = self.anim.run("eye_position_x",self.target_offset_x,self.animation_duration)
        eye_offset_y = self.anim.run("eye_position_y",self.target_offset_y,self.animation_duration)
        
        
        # 创建左眼的临时画布
        left_eye_img = Image.new("1", (22, 22), 0)
        left_eye_draw = ImageDraw.Draw(left_eye_img)
        self.draw_eye(left_eye_draw, self.left_eye_state, self.mask_rotation[0])
        # 确保坐标是整数
        img.paste(left_eye_img, (int(15+eye_offset_x), int(4+eye_offset_y)))
        
        # 创建右眼的临时画布
        right_eye_img = Image.new("1", (22, 22), 0)
        right_eye_draw = ImageDraw.Draw(right_eye_img)
        self.draw_eye(right_eye_draw, self.right_eye_state, self.mask_rotation[1])
        
        # 获取右眼区域并水平翻转
        right_eye = right_eye_img.transpose(Image.FLIP_LEFT_RIGHT)

        # 将翻转后的右眼粘贴到正确位置，确保坐标是整数
        img.paste(right_eye, (int(45+eye_offset_x), int(4+eye_offset_y)))

        return self.draw_action(img)

    def draw_action(self,img):
        if self.current_emotion == "listening":
            matrix = Matrix()
            matrix.set_matrix(PATTERN.LISTENING[int((time.time()*2)%len(PATTERN.LISTENING))])
            matrix.new() # create img
            matrix.draw()
            img.paste(matrix.img, (WIDTH - int(matrix.width * 1.6), int(3 - (time.time()*1.5)%2)))
            
        return img
    
    # 更新表情
    def update(self):
        current_time = time.time()
        
        if self.anim.is_running("eye_position_x") or self.anim.is_running("eye_position_y"):
            self.animation_duration = ANIMATION_DURATION #reset duration
                
        # 处理动画事件
        for name, queue in self.animation_queues.items():
            while queue and queue[0][0] <= current_time:
                _, callback = queue.pop(0)
                callback()
        
        # 随机眨眼（所有表情都会眨眼）
        if current_time - self.last_blink_time > self.blink_interval:
            self.blink()
            self.last_blink_time = current_time
            self.blink_interval = random.uniform(BLINK_INTERVAL, BLINK_MAX_INTERVAL)
        
        # 随机东张西望（只在neutral表情下触发）
        if (self.current_emotion == "neutral" and 
            not self.is_looking_around and
            current_time - self.last_look_around_time > self.look_around_interval):
            self.look_around()
            self.last_look_around_time = current_time
            self.look_around_interval = random.uniform(LOOK_AROUND_INTERVAL, LOOK_AROUND_MAX_INTERVAL)
        
        # 随机furrowed表情（只在neutral表情下触发）
        if (self.current_emotion == "neutral" and 
            not self.is_furrowed and
            current_time - self.last_furrowed_time > self.furrowed_interval):
            self.furrowed()
            self.last_furrowed_time = current_time
            self.furrowed_interval = random.uniform(FURROWED_INTERVAL, FURROWED_MAX_INTERVAL)
        
        return self.make_face()

    # 设置表情
    def set_emotion(self, name):
        self.animation_duration = 0.01
        self.move_eyes(0, 0)
        if self.current_emotion != name:
            self._reset_animation_states()  # 切换表情时重置所有动画状态
            if name in EMOTIONS:
                self.current_emotion = name
                expr = EMOTIONS[name]
                self.base_emotion = expr.copy()  # 保存基本表情状态
                self.left_eye_state = expr["left_eye"]
                self.right_eye_state = expr["right_eye"]
                self.mask_rotation = expr.get("mask_rotation", [0,0])
                
                # 如果表情有shake属性，执行跳动动画
                if expr.get("shake", False):
                    self.shake()
                # 如果表情有shocked属性，执行震惊动画
                if expr.get("shocked", False):
                    self.shocked()
                # 如果表情有breathe属性，执行呼吸动画
                if expr.get("breathe", False):
                    self.breathe()

    # 安排一个动画事件
    def _schedule_animation(self, name, delay, callback):
        """安排一个动画事件"""
        if name not in self.animation_queues:
            self.animation_queues[name] = []
        self.animation_queues[name].append((time.time() + delay, callback))
        # print(f"schedule {name} animation {delay}")

    # 重置所有动画状态
    def _reset_animation_states(self):
        """重置所有动画状态"""
        # 重置所有状态标志
        self.is_looking_around = False
        self.is_furrowed = False
        
        # 只保留blink队列，清空其他所有队列
        blink_queue = self.animation_queues.get("blink", [])
        self.animation_queues = {"blink": blink_queue}
        
        # 重置计时器
        self.last_look_around_time = time.time()
        self.last_furrowed_time = time.time()

    # 睁开眼睛，回到基本表情状态
    def open_eyes(self):
        """睁开眼睛，回到基本表情状态"""
        self.left_eye_state = self.base_emotion["left_eye"]
        self.right_eye_state = self.base_emotion["right_eye"]
        self.mask_rotation = self.base_emotion.get("mask_rotation", [0,0])

    # 移动眼睛
    def move_eyes(self, x, y):
        self.target_offset_x, self.target_offset_y = x, y
        self.anim.reset("eye_position_x")
        self.anim.reset("eye_position_y")

    # 东张西望动画
    def look_around(self):
        if self.is_looking_around:  # 如果正在执行，直接返回
            return
            
        def move_eyes(count=0):
            if self.current_emotion=="neutral" and count < random.uniform(3, 8): 
                # 设置目标位置
                self.move_eyes(random.randint(-LOOK_AROUND_DURATION, LOOK_AROUND_DURATION), random.randint(-LOOK_AROUND_DURATION-3, LOOK_AROUND_DURATION+3))
                
                interval = random.uniform(2, 3)
                self._schedule_animation("look_around", interval, lambda: move_eyes(count + 1))
            else:
                # 回到中心位置
                self.move_eyes(0, 0)
                self.is_looking_around = False  # 动画结束，重置标志
                    
        self.is_looking_around = True  # 设置标志
        move_eyes(0)

    # 眨眼动画
    def blink(self):
        # 不需要眨眼的表情列表
        self.no_blink_states = NO_BLINK
        
        # 检查当前表情是否需要眨眼
        if (self.current_emotion not in self.no_blink_states):
            self.left_eye_state = "relaxed"
            self.right_eye_state = "relaxed"
            self.mask_rotation = [0,0]
            self._schedule_animation("blink", 0.1, self.open_eyes)

    # 呼吸动画
    def breathe(self):
        """执行呼吸动画"""
        def do_breathe(count=0):
            if count < 100:  # 呼吸3次（上下各算一次）
                # 交替上下移动
                self.animation_duration = 1
                self.move_eyes(0, -1 if count % 2 == 0 else 1)
                self._schedule_animation("breathe", 2, lambda: do_breathe(count + 1))
            else:
                # 动画结束
                self.move_eyes(0, 0)

        
        do_breathe(0)

    # 跳动动画
    def shake(self, count=0):
        """执行上下跳动动画"""
            
        def do_shake(count):
            if count < 3:  # 跳动3次
                # 向上跳动
                self.move_eyes(0, -1)
                self._schedule_animation("shake", 0.1, lambda: do_shake_down(count))
            else:
                # 动画结束
                self.move_eyes(0, 0)
                
        def do_shake_down(count):
            # 向下跳动
            self.move_eyes(0, 2)
            self._schedule_animation("shake", 0.1, lambda: do_shake(count + 1))
        
        do_shake(0)

    # 生气动画
    def furrowed(self):
        if self.is_furrowed:  # 如果正在执行，直接返回
            return
            
        def set_furrowed():
            if self.current_emotion == "neutral":
                # 随机选择眼睛状态组合
                rand = random.random()
                if rand < 0.3:
                    self.left_eye_state, self.right_eye_state = "furrowed", "open"
                elif rand < 0.6:
                    self.left_eye_state, self.right_eye_state = "open", "furrowed"
                else:
                    self.left_eye_state = self.right_eye_state = "furrowed"
                
                # 3-5秒后恢复
                self._schedule_animation("furrowed", random.uniform(3, 5), reset_eyes)
            else:
                reset_eyes()
        
        def reset_eyes():
            self.left_eye_state = self.right_eye_state = "open"
            self.is_furrowed = False
        
        self.is_furrowed = True
        set_furrowed()

    # 震惊动画
    def shocked(self):
        """执行震惊动画"""

        def do_shocked():
            # 眼睛突然放大
            self.left_eye_state = "wide"
            self.right_eye_state = "wide"
            # 0.2秒后恢复
            self._schedule_animation("shocked", 0.2, reset_eyes)
            
        def reset_eyes():
            # 恢复到基本表情状态
            self.left_eye_state = self.base_emotion["left_eye"]
            self.right_eye_state = self.base_emotion["right_eye"]

        do_shocked()