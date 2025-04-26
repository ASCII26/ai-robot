import time

class Animation:
    def __init__(self,duration=0.3):
        self.animation_list = {}
        self.default_duration = duration

    def reset(self,id,current=0):
        '''
        重置动画
        id: 动画id
        '''
        self.animation_list[id] = {
            "current": current,
            "target": 0,
            "duration": self.default_duration,
            "start_time": time.time(),
            "obj": None,  # 存储对象引用
            "attr": None  # 存储属性名
        }

    def update(self):
        '''
        更新动画
        '''
        for id in self.animation_list:
            anim = self.animation_list[id]
            if anim["obj"] is None or anim["attr"] is None:
                continue
            if self.is_running(id):
                # 计算动画结果
                result = self.run(id, anim["target"], anim["duration"])
                # 设置新值
                setattr(anim["obj"], anim["attr"], result)
    
    def start(self, id, obj, attr, target, duration=None):
        '''
        开始动画
        id: 动画id
        obj: 要动画的对象
        attr: 要动画的属性名
        target: 目标值
        duration: 动画时长
        '''
        self.reset(id)
        anim = self.animation_list[id]
        anim["obj"] = obj
        anim["attr"] = attr
        anim["target"] = target
        anim["duration"] = duration if duration is not None else self.default_duration
        anim["current"] = getattr(obj, attr)
        
    def run(self,id,target,duration = None):
        '''
        运行动画
        id: 动画id
        target: 目标值
        duration: 动画时长
        '''
        if duration is None:
            duration = self.default_duration
        
        if self.animation_list[id]["start_time"] > 0:
            elapsed = time.time() - self.animation_list[id]["start_time"]
            if elapsed < duration:
                current = self.animation_list[id]["current"]
                progress = elapsed / duration
                # 使用缓动函数使动画更自然
                progress = progress * progress * (3 - 2 * progress)  # 平滑缓动 ease-in-out

                current = current + (target - current) * progress
                self.animation_list[id]["current"] = current
                
                return current
            else:
                self.animation_list[id]["start_time"] = 0
                return target
        
        return target

    def is_running(self,id):
        '''
        判断动画是否正在运行
        id: 动画id
        '''
        return self.animation_list[id]["start_time"] > 0
