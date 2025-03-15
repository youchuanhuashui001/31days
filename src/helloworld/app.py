"""
My first application
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW


class HelloWorld(toga.App):
    def startup(self):
        """Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """
        # 创建主容器，使用垂直布局
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        # 创建一个显示 "Hello World" 的标签
        hello_label = toga.Label(
            'Hello World!',
            style=Pack(padding=20, font_size=20, text_align='center')
        )
        
        # 将标签添加到主容器
        main_box.add(hello_label)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()


def main():
    return HelloWorld()
