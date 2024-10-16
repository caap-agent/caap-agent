import tkinter as tk
import os
from datetime import datetime

from src._base_window import BaseWindow
from src.supports import demo_recorder_support
from src.utils.tk_window_util import tk_window_config


class DemoRecorder(BaseWindow):

    def __init__(self, func):
        BaseWindow.__init__(self,
                            func=func,
                            title="Demo Recorder (Human-Mode)",
                            width=500,
                            height=500,
                            support=demo_recorder_support)

        # Folders

        # DATA
        self.record_state = None
        self.FLAG__mouse_down = False
        self.action_list = []

        # Layout
        tk_window_config(self.win, self.data_path, os.path.basename(__file__))
        self.draw_layout()

        # Update
        self.update()

    def draw_layout(self):
        frame = tk.Frame(self.win)
        frame.pack(padx=5, pady=5, fill='x', side='bottom')
        button = tk.Button(frame, width=20, text="update",
                           command=self.update)
        button.pack()

        frame = tk.Frame(self.win, name='savepath_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__SavePath(frame)

        frame = tk.Frame(self.win, name='operations_frame')
        frame.pack(padx=5, pady=5)
        self.fill_frame__Operations(frame)

        frame = tk.Frame(self.win, name='listbox_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__ListBox(frame)

    def fill_frame__SavePath(self, frame):

        button = tk.Button(frame, width=8, height=1, text="DIR",
                           command=lambda: os.startfile(os.path.abspath(self.demo_folder_path)))
        button.pack(side='left')

        button = tk.Button(frame, width=8, height=1, text="New",
                           command=self.new_folder)
        button.pack(side='left')

        txt_label = tk.Label(frame, text="  ")
        txt_label.pack(side='left')

        txt_label = tk.Label(frame, text="...", name='path_text')
        txt_label.pack(side='left')

    def new_folder(self):

        env_name = self.ask_main_controller("env_name")
        env_name = env_name.replace("-", "_")
        seed_num = self.ask_main_controller("seed_num")
        time_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
        record_folder_name = f"{env_name}_{seed_num}__{time_tag}"

        self.record_folder_path = os.path.join(self.demo_folder_path, record_folder_name)
        self.reset()


    def fill_frame__Operations(self, frame):

        canvas = tk.Canvas(frame, width=40, height=30, name='canvas')
        canvas.pack(side='left')

        button = tk.Button(frame,  width=10, height=2, text="REC", name='rec',
                           command=self.rec)
        button.pack(side='left')

        button = tk.Button(frame,  width=10, height=2, text="STOP", name='stop',
                           command=self.stop)
        button.pack(side='left')

        button = tk.Button(frame,  width=10, height=2, text="DELETE &\nRESET", name='reset',
                           command=self.reset)
        button.pack(side='left')

    def rec(self):
        demo_recorder_support.rec(self)

    def collect_actions(self):
        demo_recorder_support.collect_actions(self)

    def stop(self):
        demo_recorder_support.stop(self)

    def reset(self):
        demo_recorder_support.reset(self)


    def fill_frame__ListBox(self, frame):

        listbox = tk.Listbox(frame, width=700, height=100, exportselection=False)
        v_scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        h_scrollbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=listbox.xview)

        h_scrollbar.pack(side='bottom', fill=tk.X)
        v_scrollbar.pack(side='right', fill=tk.Y)
        listbox.pack(side='right', fill ='both')

        listbox.config(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        v_scrollbar.config(command = listbox.yview)
        h_scrollbar.config(command = listbox.xview)
