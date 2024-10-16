import tkinter as tk
import os
import json
import shutil

from src._base_window import BaseWindow
from src.supports import demo_scripter_support
from src.utils.tk_window_util import tk_window_config
from src.utils.file import read_text_file


class DemoScripter(BaseWindow):

    def __init__(self, func):
        BaseWindow.__init__(self,
                            func=func,
                            title="Demo Scripter",
                            width=500,
                            height=500,
                            support=demo_scripter_support)

        # Folders

        # Data
        self.record_folder = None
        self.functions = None  # to be filled at fill_frame__Functions
        self.action_list = []

        self.FLAG__new_answer = None
        self.prompt = ""
        self.answer = ""

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

        frame = tk.Frame(self.win, name='path_settings_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__PathSettings(frame)

        frame = tk.Frame(self.win, name='functions_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__Functions(frame)

        frame = tk.Frame(self.win, name='listbox_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__listbox(frame)

        frame = tk.Frame(self.win, name='convert_frame')
        frame.pack(padx=5, pady=0, fill='x')
        self.fill_frame__convert(frame)

        frame = tk.Frame(self.win, name='script_frame')
        frame.pack(padx=5, pady=5,  fill='both')
        self.fill_frame__script(frame)

    def fill_frame__PathSettings(self, frame):

        button = tk.Button(frame, width=8, height=1, text="DIR",
                           command=lambda: os.startfile(os.path.abspath(self.demo_folder_path)))
        button.pack(side='left')

        button = tk.Button(frame, width=8, height=1, text="Load",
                           command=self.load)
        button.pack(side='left')

        txt_label = tk.Label(frame, text="  ")
        txt_label.pack(side='left')

        txt_label = tk.Label(frame, text="...", name='path_text')
        txt_label.pack(side='left')

    def load(self):
        demo_scripter_support.load(self)


    def fill_frame__Functions(self, frame):

        function_json_files = [f for f in os.listdir("./functions") if f.endswith('.json')]
        function_json_files.sort()
        default_functions_json = function_json_files[-1]
        functions_json_fullpath = os.path.join("./functions", default_functions_json)

        json_data = read_text_file(functions_json_fullpath)
        self.functions = json.loads(json_data)

        txt_label = tk.Label(frame, text="  Used Functions: ")
        txt_label.pack(side='left')

        txt_label = tk.Label(frame, text=default_functions_json, name='functions_filename_text')
        txt_label.pack(side='left')





    def fill_frame__listbox(self, frame):

        listbox = tk.Listbox(frame, width=100, height=10,  exportselection=False)
        v_scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        h_scrollbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=listbox.xview)
        listbox.config(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)

        h_scrollbar.pack(side='bottom', fill=tk.X)
        v_scrollbar.pack(side='right', fill=tk.Y)
        listbox.pack(side='right', fill ='both', expand=True)



    def fill_frame__convert(self, frame):

        subframe = tk.Frame(frame)
        subframe.pack(side='left', fill='x')
        button = tk.Button(subframe, width=15, height=2, text="View @\nAnnotator",
                           command=self.view_at_annotator)
        button.pack(side='left')

        subframe = tk.Frame(frame)
        subframe.pack(side='left', fill='x', expand=True)

        subframe = tk.Frame(frame)
        subframe.pack(side='left', fill='x')
        button = tk.Button(subframe, width=15, height=2, text="Convert",
                           command=self.convert)
        button.pack(side='left')
        button = tk.Button(subframe, width=5, height=2, text="to\nEND",
                           command=self.convert_to_end)
        button.pack(side='left')

        subframe = tk.Frame(frame)
        subframe.pack(side='left', fill='x', expand=True)

        subframe = tk.Frame(frame)
        subframe.pack(side='left', fill='x')
        button = tk.Button(subframe, width=15, height=2, text="Add Reason",
                           command=self.add_reason)
        button.pack(side='left')
        button = tk.Button(subframe, width=5, height=2, text="to\nEND",
                           command=self.add_reason_to_end)
        button.pack(side='left')

        subframe = tk.Frame(frame)
        subframe.pack(side='left', fill='x', expand=True)
        subframe = tk.Frame(frame)
        subframe.pack(side='left', fill='x', expand=True)

        button = tk.Button(frame, width=15, height=2, text="Save Script",
                           command=self.save_script)
        button.pack(side='right')

    def view_at_annotator(self):
        demo_scripter_support.view_at_annotator(self)

    def convert(self):
        demo_scripter_support.convert(self)
    def convert_to_end(self):
        demo_scripter_support.convert_to_end(self)

    def add_reason(self):
        demo_scripter_support.add_reason(self)
    def add_reason_to_end(self):
        demo_scripter_support.add_reason_to_end(self)

    def save_script(self):
        demo_scripter_support.save_script(self)



    def fill_frame__script(self, frame):

        text = tk.Text(frame, height=130, width=120, name='script_text')
        v_scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
        text.config(yscrollcommand=v_scrollbar.set)

        v_scrollbar.pack(side='right', fill='y')
        text.pack(side='right', fill ='both', expand=True)


    def _ready_temp_folder(self):
        # Check if the folder exists
        if os.path.exists(self.temp_folder):
            # If it exists, delete everything inside it
            for file_name in os.listdir(self.temp_folder):
                file_path = os.path.join(self.temp_folder, file_name)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
            # Delete the folder itself
            os.rmdir(self.temp_folder)

        # Create a new folder at the same path
        os.mkdir(self.temp_folder)
