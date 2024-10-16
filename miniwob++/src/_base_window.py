import os
import importlib
import tkinter as tk
from src.utils import file
from src.utils import elements_util
from src.utils import screenshot_util
from src.utils import tk_window_util
from src.utils import breakdown


class BaseWindow:

    def __init__(self, func, title:str, width:int, height:int, support):

        # From Master
        self.ask_main_controller = func
        self.data_path = self.ask_main_controller('data_path')

        # Window
        self.win = tk.Toplevel()
        self.win.title(title)
        self.win.geometry(f"{width}x{height}")

        # Support
        self.support = support

        # Folders
        self.demo_folder_path = os.path.join(self.data_path, "human_demo_record")
        self.script_folder_path = os.path.join(self.data_path, "human_demo_scripts")
        self.temp_folder_path = os.path.join(self.data_path, "_temp")
        self.result_folder = os.path.join(self.data_path, "llm_agent_record")
        self.blank_folder = os.path.join(self.data_path, "human_demo_record/_blank")
        self.record_folder_path = None
        self.project_folder = None
        self.job_folder = None

        os.makedirs(self.demo_folder_path, exist_ok=True)
        os.makedirs(self.script_folder_path, exist_ok=True)
        os.makedirs(self.temp_folder_path, exist_ok=True)
        os.makedirs(self.result_folder, exist_ok=True)
        os.makedirs(self.blank_folder, exist_ok=True)

    def update(self):
        importlib.reload(self.support)
        importlib.reload(file)
        importlib.reload(elements_util)
        importlib.reload(screenshot_util)
        importlib.reload(tk_window_util)
        importlib.reload(breakdown)
        self.support.update(self)
