"""
31 Days 应用

一个用于跟踪需要连续31天打卡的任务的应用程序。
"""

import os
import json
import datetime
from pathlib import Path

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW


class Task:
    """需要31天打卡才能完成的任务。"""
    
    def __init__(self, name, id=None, created_at=None, check_ins=None, rounds=1):
        self.id = id or str(int(datetime.datetime.now().timestamp()))
        self.name = name
        self.created_at = created_at or datetime.datetime.now().isoformat()
        self.check_ins = check_ins or []  # 现在存储的是 {date, time, note} 的字典列表
        self.rounds = rounds  # 当前轮次（1=第一轮，2=第二轮，等等）
    
    @property
    def days_required(self):
        """当前轮次所需的天数。"""
        return 31 * self.rounds
    
    @property
    def days_completed(self):
        """当前轮次已完成的天数。"""
        return len(self.check_ins)
    
    @property
    def is_completed(self):
        """任务是否已完成当前轮次。"""
        return self.days_completed >= self.days_required
    
    @property
    def can_check_in_today(self):
        """今天是否可以打卡。"""
        today = datetime.date.today().isoformat()
        # 检查是否已经有今天的打卡记录
        for check_in in self.check_ins:
            if isinstance(check_in, dict) and check_in.get('date') == today:
                return False
            elif isinstance(check_in, str) and check_in == today:
                return False
        return True
    
    def check_in(self, note=""):
        """今天打卡，可以添加备注。"""
        if self.can_check_in_today:
            today = datetime.date.today().isoformat()
            now = datetime.datetime.now().strftime('%H:%M:%S')
            
            # 创建包含日期、时间和备注的打卡记录
            check_in_record = {
                'date': today,
                'time': now,
                'note': note
            }
            
            self.check_ins.append(check_in_record)
            return True
        return False
    
    def start_next_round(self):
        """开始任务的下一轮。"""
        if self.is_completed:
            self.rounds += 1
            return True
        return False
    
    def to_dict(self):
        """将任务转换为字典以便序列化。"""
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at,
            'check_ins': self.check_ins,
            'rounds': self.rounds
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建任务。"""
        # 兼容旧版本数据
        check_ins = data.get('check_ins', [])
        # 如果是旧版本数据（字符串列表），转换为新格式（字典列表）
        if check_ins and isinstance(check_ins[0], str):
            new_check_ins = []
            for date_str in check_ins:
                new_check_ins.append({
                    'date': date_str,
                    'time': '00:00:00',  # 旧数据没有时间信息
                    'note': ''  # 旧数据没有备注
                })
            check_ins = new_check_ins
            
        return cls(
            name=data['name'],
            id=data['id'],
            created_at=data['created_at'],
            check_ins=check_ins,
            rounds=data['rounds']
        )


class ThirtyOneDaysApp(toga.App):
    def startup(self):
        """构建并显示Toga应用程序。"""
        # 从存储中加载任务
        self.tasks = self.load_tasks()
        
        # 主布局
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        # 顶部区域（标题和添加按钮）
        top_box = toga.Box(style=Pack(direction=ROW, padding=5))
        
        # 应用标题
        title_label = toga.Label(
            '31 Days',
            style=Pack(padding=(0, 5), font_size=24, font_weight='bold', text_align='center', flex=1)
        )
        top_box.add(title_label)
        
        # 添加任务按钮（放在右上角）
        add_button = toga.Button(
            '+',
            on_press=self.show_add_task_dialog,
            style=Pack(width=40, height=40, font_size=20)
        )
        top_box.add(add_button)
        
        main_box.add(top_box)
        
        # 任务容器
        self.tasks_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        
        # 空状态消息
        self.empty_state = toga.Label(
            '还没有任务。点击右上角的 + 按钮添加新任务！',
            style=Pack(padding=20, font_size=16, text_align='center')
        )
        self.tasks_box.add(self.empty_state)
        
        # 任务滚动容器
        tasks_scroll = toga.ScrollContainer(horizontal=False)
        tasks_scroll.content = self.tasks_box
        tasks_scroll.style.update(height=450, padding=5)
        main_box.add(tasks_scroll)
        
        # 创建主窗口
        self.main_window = toga.MainWindow(title='31 Days')
        self.main_window.content = main_box
        
        # 刷新任务列表
        self.refresh_tasks()
        
        # 显示主窗口
        self.main_window.show()
    
    def load_tasks(self):
        """从存储中加载任务。"""
        try:
            data_path = Path(self.paths.data) / 'tasks.json'
            if data_path.exists():
                with open(data_path, 'r') as f:
                    tasks_data = json.load(f)
                return [Task.from_dict(task_data) for task_data in tasks_data]
            return []
        except Exception as e:
            print(f"加载任务时出错: {e}")
            return []
    
    def save_tasks(self):
        """保存任务到存储。"""
        try:
            data_path = Path(self.paths.data) / 'tasks.json'
            data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(data_path, 'w') as f:
                tasks_data = [task.to_dict() for task in self.tasks]
                json.dump(tasks_data, f)
        except Exception as e:
            print(f"保存任务时出错: {e}")
    
    def refresh_tasks(self):
        """刷新任务列表显示。"""
        # 清除任务框
        for child in list(self.tasks_box.children):
            self.tasks_box.remove(child)
        
        # 如果没有任务，显示空状态
        if not self.tasks:
            self.tasks_box.add(self.empty_state)
            return
        
        # 将每个任务添加到显示中
        for task in self.tasks:
            task_box = self.create_task_widget(task)
            self.tasks_box.add(task_box)
    
    def create_task_widget(self, task):
        """创建显示任务的小部件。"""
        # 任务容器
        task_box = toga.Box(style=Pack(direction=COLUMN, padding=10, background_color='#f0f0f0'))
        
        # 任务标题（名称和进度）
        header_box = toga.Box(style=Pack(direction=ROW, padding=5))
        
        # 任务名称
        name_label = toga.Label(
            task.name,
            style=Pack(flex=1, font_weight='bold', font_size=16)
        )
        header_box.add(name_label)
        
        # 进度标签
        progress_label = toga.Label(
            f"{task.days_completed}/{task.days_required} 天",
            style=Pack(width=100, text_align='right')
        )
        header_box.add(progress_label)
        
        task_box.add(header_box)
        
        # 进度条
        progress = task.days_completed / task.days_required
        progress_bar = toga.ProgressBar(max=1.0, value=progress)
        progress_bar.style.update(height=20, padding=(0, 5, 5, 5))
        task_box.add(progress_bar)
        
        # 按钮容器
        buttons_box = toga.Box(style=Pack(direction=ROW, padding=5))
        
        # 打卡按钮
        check_in_button = toga.Button(
            '打卡',
            on_press=lambda widget: self.check_in_task(task),
            style=Pack(flex=1, padding=3)
        )
        check_in_button.enabled = task.can_check_in_today and not task.is_completed
        buttons_box.add(check_in_button)
        
        # 下一轮按钮（仅当任务完成时可见）
        if task.is_completed:
            next_round_button = toga.Button(
                f'开始第 {task.rounds + 1} 轮',
                on_press=lambda widget: self.start_next_round(task),
                style=Pack(flex=1, padding=3)
            )
            buttons_box.add(next_round_button)
        
        # 详情按钮
        details_button = toga.Button(
            '详情',
            on_press=lambda widget: self.show_task_details(task),
            style=Pack(flex=1, padding=3)
        )
        buttons_box.add(details_button)
        
        # 删除按钮
        delete_button = toga.Button(
            '删除',
            on_press=lambda widget: self.delete_task(task),
            style=Pack(flex=1, padding=3)
        )
        buttons_box.add(delete_button)
        
        task_box.add(buttons_box)
        
        return task_box
    
    def show_add_task_dialog(self, widget):
        """显示添加任务对话框"""
        # 创建添加任务页面
        add_task_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        # 保存当前主窗口内容
        self.previous_content = self.main_window.content
        
        # 标题
        title_label = toga.Label(
            '添加新任务',
            style=Pack(padding=(5, 5), font_size=20, font_weight='bold', text_align='center')
        )
        add_task_box.add(title_label)
        
        # 输入框
        input_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        input_label = toga.Label(
            '任务名称:',
            style=Pack(padding=(0, 5))
        )
        input_box.add(input_label)
        
        self.task_input = toga.TextInput(style=Pack(padding=(0, 5)))
        input_box.add(self.task_input)
        
        add_task_box.add(input_box)
        
        # 按钮区域
        buttons_box = toga.Box(style=Pack(direction=ROW, padding=5))
        
        # 取消按钮
        cancel_button = toga.Button(
            '取消',
            on_press=self.close_add_task_dialog,
            style=Pack(flex=1, padding=5)
        )
        buttons_box.add(cancel_button)
        
        # 确认按钮
        confirm_button = toga.Button(
            '添加',
            on_press=self.add_task,
            style=Pack(flex=1, padding=5)
        )
        buttons_box.add(confirm_button)
        
        add_task_box.add(buttons_box)
        
        # 设置主窗口内容为添加任务页面
        self.main_window.content = add_task_box
    
    def close_add_task_dialog(self, widget):
        """关闭添加任务对话框"""
        if hasattr(self, 'previous_content'):
            self.main_window.content = self.previous_content
    
    def add_task(self, widget):
        """从输入框添加新任务。"""
        task_name = self.task_input.value
        if task_name:
            new_task = Task(name=task_name)
            self.tasks.append(new_task)
            self.save_tasks()
            # 返回主界面
            self.close_add_task_dialog(widget)
            self.refresh_tasks()
            # 显示添加成功消息
            self.show_notification(f'已添加任务"{task_name}"')
        else:
            # 显示错误消息
            self.show_notification('请输入任务名称')
    
    def check_in_task(self, task):
        """为任务打卡。"""
        if not task.can_check_in_today:
            self.show_notification('今天已经打过卡了。')
            return
            
        # 创建打卡页面
        check_in_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        # 保存当前主窗口内容
        self.previous_content = self.main_window.content
        self.current_task = task
        
        # 标题
        title_label = toga.Label(
            f'为"{task.name}"打卡',
            style=Pack(padding=(5, 5), font_size=20, font_weight='bold', text_align='center')
        )
        check_in_box.add(title_label)
        
        # 备注输入框
        input_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        input_label = toga.Label(
            '备注（可选）:',
            style=Pack(padding=(0, 5))
        )
        input_box.add(input_label)
        
        self.note_input = toga.MultilineTextInput(style=Pack(padding=(0, 5), height=100))
        input_box.add(self.note_input)
        
        check_in_box.add(input_box)
        
        # 按钮区域
        buttons_box = toga.Box(style=Pack(direction=ROW, padding=5))
        
        # 取消按钮
        cancel_button = toga.Button(
            '取消',
            on_press=self.close_check_in_dialog,
            style=Pack(flex=1, padding=5)
        )
        buttons_box.add(cancel_button)
        
        # 确认按钮
        confirm_button = toga.Button(
            '打卡',
            on_press=self.confirm_check_in,
            style=Pack(flex=1, padding=5)
        )
        buttons_box.add(confirm_button)
        
        check_in_box.add(buttons_box)
        
        # 设置主窗口内容为打卡页面
        self.main_window.content = check_in_box
    
    def close_check_in_dialog(self, widget):
        """关闭打卡对话框"""
        if hasattr(self, 'previous_content'):
            self.main_window.content = self.previous_content
    
    def confirm_check_in(self, widget):
        """确认打卡"""
        if hasattr(self, 'current_task'):
            note = self.note_input.value if hasattr(self, 'note_input') else ""
            if self.current_task.check_in(note):
                self.save_tasks()
                # 返回主界面
                if hasattr(self, 'previous_content'):
                    self.main_window.content = self.previous_content
                self.refresh_tasks()
                # 显示打卡成功消息
                now = datetime.datetime.now().strftime('%H:%M:%S')
                self.show_notification(f'已为"{self.current_task.name}"打卡！\n时间: {now}\n进度: {self.current_task.days_completed}/{self.current_task.days_required} 天')
    
    def show_notification(self, message):
        """显示通知消息，2秒后自动关闭"""
        # 创建一个简单的通知框
        notification_box = toga.Box(style=Pack(
            direction=COLUMN, 
            padding=5, 
            background_color='#4CAF50',  # 绿色背景
            color='white',
            width=200,
            height=50
        ))
        
        # 消息内容
        message_label = toga.Label(
            message,
            style=Pack(padding=5, color='white', text_align='center')
        )
        notification_box.add(message_label)
        
        # 将通知框添加到主窗口
        main_content = self.main_window.content
        
        # 创建一个容器来放置通知框，使其显示在顶部中央
        overlay_box = toga.Box(style=Pack(
            direction=COLUMN,
            alignment='center',
            flex=1
        ))
        overlay_box.add(notification_box)
        
        # 创建一个新的主容器，包含原有内容和覆盖层
        container = toga.Box(style=Pack(direction=COLUMN))
        container.add(main_content)
        container.add(overlay_box)
        
        # 设置为主窗口内容
        self.main_window.content = container
        
        # 保存原始内容，以便关闭通知时恢复
        self.original_content = main_content
        
        # 使用定时器在2秒后自动关闭通知
        self.add_background_task(self.auto_close_notification)
    
    def auto_close_notification(self, **kwargs):
        """2秒后自动关闭通知"""
        import time
        time.sleep(2)  # 等待2秒
        
        # 在主线程中关闭通知
        self.add_background_task(self._close_notification_on_main_thread)
    
    def _close_notification_on_main_thread(self, **kwargs):
        """在主线程中关闭通知"""
        if hasattr(self, 'original_content'):
            self.main_window.content = self.original_content
    
    def start_next_round(self, task):
        """开始任务的下一轮。"""
        if task.start_next_round():
            self.save_tasks()
            self.refresh_tasks()
            self.show_notification(f'已开始"{task.name}"的第 {task.rounds} 轮！\n新目标：{task.days_required} 天')
    
    def show_task_details(self, task):
        """显示任务详情。"""
        # 在 Android 上，我们不能创建次要窗口，所以使用内联方式显示详情
        
        # 保存当前主窗口内容
        self.previous_content = self.main_window.content
        
        # 创建详情页面
        detail_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        # 返回按钮
        back_button = toga.Button(
            '← 返回',
            on_press=self.close_task_details,
            style=Pack(padding=5)
        )
        detail_box.add(back_button)
        
        # 任务标题
        title_label = toga.Label(
            f"详情: {task.name}",
            style=Pack(padding=(5, 5), font_size=20, font_weight='bold', text_align='center')
        )
        detail_box.add(title_label)
        
        # 任务信息
        info_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        
        # 创建日期
        created_date = datetime.datetime.fromisoformat(task.created_at).strftime('%Y-%m-%d')
        created_label = toga.Label(
            f"创建日期: {created_date}",
            style=Pack(padding=(0, 5))
        )
        info_box.add(created_label)
        
        # 当前轮次
        round_label = toga.Label(
            f"当前轮次: {task.rounds}",
            style=Pack(padding=(0, 5))
        )
        info_box.add(round_label)
        
        # 进度
        progress_label = toga.Label(
            f"进度: {task.days_completed}/{task.days_required} 天",
            style=Pack(padding=(0, 5))
        )
        info_box.add(progress_label)
        
        detail_box.add(info_box)
        
        # 打卡历史标题
        checkins_title = toga.Label(
            "打卡历史:",
            style=Pack(padding=(10, 5), font_weight='bold')
        )
        detail_box.add(checkins_title)
        
        # 打卡历史列表
        checkins_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        
        if task.check_ins:
            for check_in_record in sorted(task.check_ins, key=lambda x: x['date'] if isinstance(x, dict) else x, reverse=True):
                if isinstance(check_in_record, dict):
                    # 新版本数据格式
                    date_str = check_in_record['date']
                    time_str = check_in_record.get('time', '00:00:00')
                    note = check_in_record.get('note', '')
                    
                    # 创建打卡记录容器
                    record_box = toga.Box(style=Pack(direction=COLUMN, padding=5, background_color='#f5f5f5'))
                    
                    # 日期和时间
                    date_time_label = toga.Label(
                        f"{date_str} {time_str}",
                        style=Pack(padding=(0, 2), font_weight='bold')
                    )
                    record_box.add(date_time_label)
                    
                    # 如果有备注，显示备注
                    if note:
                        note_label = toga.Label(
                            f"备注: {note}",
                            style=Pack(padding=(0, 2))
                        )
                        record_box.add(note_label)
                    
                    checkins_box.add(record_box)
                else:
                    # 旧版本数据格式（仅日期字符串）
                    date_label = toga.Label(
                        check_in_record,
                        style=Pack(padding=(0, 2))
                    )
                    checkins_box.add(date_label)
        else:
            no_checkins_label = toga.Label(
                "还没有打卡记录。",
                style=Pack(padding=(0, 5))
            )
            checkins_box.add(no_checkins_label)
        
        # 滚动容器
        checkins_scroll = toga.ScrollContainer(horizontal=False)
        checkins_scroll.content = checkins_box
        checkins_scroll.style.update(height=300, padding=5)
        detail_box.add(checkins_scroll)
        
        # 设置主窗口内容为详情页面
        self.main_window.content = detail_box
    
    def close_task_details(self, widget):
        """关闭任务详情，返回主界面"""
        if hasattr(self, 'previous_content'):
            self.main_window.content = self.previous_content
    
    def delete_task(self, task):
        """删除任务。"""
        # 显示确认对话框
        # 保存当前主窗口内容和要删除的任务
        self.previous_content = self.main_window.content
        self.task_to_delete = task
        
        # 创建确认对话框
        confirm_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        # 标题
        title_label = toga.Label(
            '确认删除',
            style=Pack(padding=(5, 5), font_size=20, font_weight='bold', text_align='center')
        )
        confirm_box.add(title_label)
        
        # 提示信息
        message_label = toga.Label(
            f'确定要删除任务"{task.name}"吗？\n此操作不可撤销。',
            style=Pack(padding=20, text_align='center')
        )
        confirm_box.add(message_label)
        
        # 按钮区域
        buttons_box = toga.Box(style=Pack(direction=ROW, padding=5))
        
        # 取消按钮
        cancel_button = toga.Button(
            '取消',
            on_press=self.cancel_delete_task,
            style=Pack(flex=1, padding=5)
        )
        buttons_box.add(cancel_button)
        
        # 确认按钮
        confirm_button = toga.Button(
            '删除',
            on_press=self.confirm_delete_task,
            style=Pack(flex=1, padding=5)
        )
        buttons_box.add(confirm_button)
        
        confirm_box.add(buttons_box)
        
        # 设置主窗口内容为确认对话框
        self.main_window.content = confirm_box
    
    def cancel_delete_task(self, widget):
        """取消删除任务"""
        if hasattr(self, 'previous_content'):
            self.main_window.content = self.previous_content
    
    def confirm_delete_task(self, widget):
        """确认删除任务"""
        if hasattr(self, 'task_to_delete'):
            # 直接移除任务
            self.tasks = [t for t in self.tasks if t.id != self.task_to_delete.id]
            task_name = self.task_to_delete.name
            self.save_tasks()
            # 返回主界面
            if hasattr(self, 'previous_content'):
                self.main_window.content = self.previous_content
            self.refresh_tasks()
            # 显示删除成功消息
            self.show_notification(f'已删除任务"{task_name}"')


def main():
    return ThirtyOneDaysApp('31 Days', 'org.example.thirtyone_days')
