import random

# 绘制左侧 VU 效果（32x32 区域）
def draw_vu(draw, volume_level = 0.5,offset=0):
    bar_width = 1
    spacing = 3
    center_y = 17  # 屏幕中心点（32/2）
    num_bars = 3   # 增加到4个柱状图
    max_height = 10

    # 获取当前音量级别
    for i in range(num_bars):
        # 根据当前音量级别计算柱状图高度
        bar_height = int(max_height * min(0.8, volume_level))
        
        # 添加非常小的随机变化使显示更平滑
        if bar_height > 0:
            bar_height = max(2, min(max_height, 
                              bar_height + random.randint(-4, 4)))
        
        x = 4 + i * (bar_width + spacing) + offset
        
        # 绘制上半部分
        draw.rectangle((x, center_y - bar_height, 
                       x + bar_width, center_y), fill=255)
        
        # 绘制下半部分
        draw.rectangle((x, center_y, 
                       x + bar_width, center_y + bar_height), fill=255)

# 右侧文字滚动
def scroll_text(draw, text, x=32, y=0, step=0, font=None, is_center=False):
    text = f"{text} "
    stop_frames = 16  # 停顿的帧数
    # 计算文字宽度
    text_width = font.getlength(text)
    disp_width = 128
    available_width = disp_width - x  # 可用宽度（总宽度128减去左侧32像素）
    
    if text_width <= available_width:
        # 文字不需要滚动，直接显示
        if is_center:
            draw.text((x + (available_width - text_width) / 2, y), text, font=font, fill=255)
        else:
            draw.text((x, y), text, font=font, fill=255)
    else:
        # 文字需要滚动
        # 计算最大滚动距离
        max_scroll = text_width - available_width
        
        # 计算完整的来回滚动周期（包括停顿时间）
        full_cycle = max_scroll * 2 + stop_frames * 2  # 来回滚动的总距离加上停顿时间
        current_pos = step % full_cycle
        
        # 确定滚动方向和位置
        if current_pos <= max_scroll:
            # 向左滚动
            scroll_x = x - current_pos
        elif current_pos <= max_scroll + stop_frames:
            # 在左端停顿
            scroll_x = x - max_scroll
        elif current_pos <= max_scroll * 2 + stop_frames:
            # 向右滚动
            scroll_x = x - (max_scroll - (current_pos - max_scroll - stop_frames))
        else:
            # 在右端停顿
            scroll_x = x
        
        # 绘制文字
        draw.text((scroll_x, y), text, font=font, fill=255)

        # 遮盖左侧区域（0-31像素）
        bbox = font.getbbox(text)
        text_height = bbox[3] - bbox[1]
        draw.rectangle((x-32, y, x-1, y + text_height+2), fill=0)
