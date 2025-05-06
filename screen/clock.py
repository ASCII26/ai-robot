import time
from .base import DisplayPlugin

class ClockDisplay(DisplayPlugin):
    def __init__(self, manager, width, height):
        self.name = "clock"
        super().__init__(manager, width, height)
        self.last_blink_time = 0
        self.show_colon = True
        

    def update(self):
        self.clear()
        current_time = time.time()
        
        # handle the colon blinking
        if current_time - self.last_blink_time >= 0.5:
            self.show_colon = not self.show_colon
            self.last_blink_time = current_time
        
        # display time (large font)
        if self.show_colon:
            time_str = time.strftime("%H:%M:%S")
        else:
            time_str = time.strftime("%H %M %S")
        
        text_width = self.font16.getlength(time_str)
        x = (self.width - text_width) // 2
        y = (self.height - 16) // 2 + 4
        self.draw.text((x, y), time_str, font=self.font16, fill=255)
        
        # display date (small font, top center)
        current_date = time.strftime("%Y年%m月%d日")
        date_width = self.font8.getlength(current_date)
        x_date = (self.width - date_width) // 2
        y_date = 0
        self.draw.text((x_date, y_date), "" + current_date, font=self.font_status, fill=255)
