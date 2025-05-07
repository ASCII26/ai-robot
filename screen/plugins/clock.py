import time
from screen.base import DisplayPlugin
from ui.component import draw_scroll_text


class clock(DisplayPlugin):
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

        draw_scroll_text(
            self.draw, time_str, (0, 12), width=128, font=self.font16, align="center"
        )

        # display date (small font, top center)
        current_date = time.strftime("%Y年%m月%d日")
        draw_scroll_text(
            self.draw,
            "" + current_date,
            (-2, 2),
            width=128,
            font=self.font8,
            align="center",
        )
