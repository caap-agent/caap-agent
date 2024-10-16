import tkinter as tk
from tkinter import ttk
import os

from src._base_window import BaseWindow
from src.supports import llm_recorder_support
from src.utils.tk_window_util import tk_window_config
from src import get_logger
logger = get_logger(logger_name=__file__)

class LLMRecorder(BaseWindow):

    def __init__(self, func):
        BaseWindow.__init__(self,
                            func=func,
                            title="LLM Agent Recorder",
                            width=500,
                            height=500,
                            support=llm_recorder_support)

        # Folders

        # DATA
        self.functions_folder_name_FIXED = "functions"  # folder used inside job_folder
        self.demo_folder_name_FIXED = "demo"  # folder used inside job_folder
        self.job_seed = None  # safety measure
        self.job_status = None
        self.job_reward = None
        self.functions_folder = None
        self.demo_folder = None
        self.demo_content_list = []
        self.action_list = []
        self.screen_history = []
        self.selected = -1
        self.do_multi_action = False

        self.FLAG__disable_record = False
        self.is_invalid = False

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

        frame = tk.Frame(self.win, name='project_name_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__ProjectName(frame)

        frame = tk.Frame(self.win, name='job_name_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__JobName(frame)

        frame = tk.Frame(self.win, name='job_folder_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__JobFolder(frame)

        separator = ttk.Separator(self.win, orient='horizontal')
        separator.pack(fill='x', padx=5, pady=5)

        frame = tk.Frame(self.win, name='functions_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__Functions(frame)

        frame = tk.Frame(self.win, name='demo_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__Demo(frame)

        frame = tk.Frame(self.win, name='two_column_frame')
        frame.pack(padx=5, pady=5, fill='x', expand = True)

        subframe = tk.Frame(frame, name='operations_subframe')
        subframe.pack(expand=True, fil ='both', side='right')
        self.fill_frame__Operations(subframe)

        subframe = tk.Frame(frame, name='listbox_subframe')
        subframe.pack(expand=True, fill='both', side='left')
        self.fill_frame__ListBox(subframe)

    def fill_frame__ProjectName(self, frame):

        button = tk.Button(frame, width=5, height=1, text="DIR",
                           command=lambda: os.startfile(os.path.abspath(self.result_folder)))
        button.pack(side='left')

        button = tk.Button(frame, width=5, height=1, text="New",
                           command=self.new_project)
        button.pack(side='left')

        button = tk.Button(frame, width=5, height=1, text="Load",
                           command=self.load_project)
        button.pack(side='left')

        txt_label = tk.Label(frame, text="  Project Name: ", name='project_name_text')
        txt_label.pack(side='left')

        entry = tk.Entry(frame, width=50)
        entry.insert(0, "Hello, world!")
        entry.config(state="readonly")
        entry.pack(side='left')

    def new_project(self):
        llm_recorder_support.new_project(self)

    def load_project(self, project_folder=None):
        llm_recorder_support.load_project(self, project_folder)

    def fill_frame__JobName(self, frame):

        button = tk.Button(frame, width=5, height=1, text="DIR",
                           command=lambda: os.startfile(os.path.abspath(self.project_folder)))
        button.pack(side='left')

        button = tk.Button(frame, width=5, height=1, text="New",
                           command=self.new_job)
        button.pack(side='left')

        button = tk.Button(frame, width=5, height=1, text="Load",
                           command=self.load_job)
        button.pack(side='left')

        txt_label = tk.Label(frame, text="       Job Name: ", name='job_name_text')
        txt_label.pack(side='left')

        entry = tk.Entry(frame, width=50)
        entry.insert(0, "Hello, world!")
        entry.config(state="readonly")
        entry.pack(side='left')

    def new_job(self):
        llm_recorder_support.new_job(self)

    def load_job(self):
        llm_recorder_support.load_job(self)

    def fill_frame__JobFolder(self, frame):

        subframe = tk.Frame(frame)
        subframe.pack(side='left', fill='x', expand=True)
        button = tk.Button(subframe, width=25, height=1, text="Show Job in Explorer",
                           command=lambda: os.startfile(os.path.abspath(self.job_folder)))
        button.pack(side='top')

        subframe = tk.Frame(frame)
        subframe.pack(side='right')
        button = tk.Button(subframe, width=10, height=1, text="preset_1",
                           command=self.preset_1)
        button.pack(side='left')

    def preset_1(self):
        llm_recorder_support.preset_1(self)

    def fill_frame__Functions(self, frame):

        txt_label = tk.Label(frame, text="  Used Functions: ")
        txt_label.pack(side='left')

        txt_label = tk.Label(frame, text="...", name='functions_filename_text')
        txt_label.pack(side='left')



    def fill_frame__Demo(self, frame):

        txt_label = tk.Label(frame, text="  Used Demo Count: ")
        txt_label.pack(side='left')

        txt_label = tk.Label(frame, text="...", name='demo_count_text')
        txt_label.pack(side='left')

        txt_label = tk.Label(frame, text="  ", name='spacer')
        txt_label.pack(side='left')

        button = tk.Button(frame, width=10, height=1, text="Add Demo",
                           command=self.add_demo)
        button.pack(side='left')

    def add_demo(self, file_path_tuple=None):
        llm_recorder_support.add_demo(self, file_path_tuple)



    def fill_frame__ListBox(self, frame):

        listbox = tk.Listbox(frame, width=100, height=100, exportselection=False)
        v_scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        h_scrollbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=listbox.xview)

        h_scrollbar.pack(side='bottom', fill=tk.X)
        v_scrollbar.pack(side='right', fill=tk.Y)
        listbox.pack(side='left', fill='both')

        listbox.config(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        v_scrollbar.config(command=listbox.yview)
        h_scrollbar.config(command=listbox.xview)

        listbox.bind('<<ListboxSelect>>', self.onselect)

    def onselect(self, event):
        listbox = event.widget
        selection = listbox.curselection()
        if not selection:
            self.selected = -1
        else:
            self.selected = selection[0]

        self.update()


    def fill_frame__Operations(self, frame):

        img_frame = tk.Frame(frame, name='image_process')
        img_frame.pack(fill='x')

        subframe = tk.Frame(img_frame, name='visualobserver_group')
        subframe.pack(padx=5, pady=5, side='left')
        button = tk.Button(subframe, width=12, height=3, text="Send to\nVisual Observer",
                           command=self.button_click__send_to_visualobserver)
        button.pack()
        button = tk.Button(subframe, width=12, height=2, text="Import",
                           command=self.import_visualobserver)
        button.pack()

        subframe = tk.Frame(img_frame, name='annotator_group')
        subframe.pack(padx=5, pady=5, side='right')
        button = tk.Button(subframe, width=12, height=3, text="Send to\nAnnotator",
                           command=self.button_click__send_to_annotator)
        button.pack()
        button = tk.Button(subframe, width=12, height=2, text="Import",
                           command=self.import_annotator)
        button.pack()

        txt_label = tk.Label(frame, text="")  # spacer
        txt_label.pack()

        button = tk.Button(frame, width=18, height=3, text="Send to\nCAAP Prompter",
                           command=self.button_click__send_to_caap_prompter)
        button.pack()
        button = tk.Button(frame, width=18, height=2, text="ACT",
                           command=self.act_by_caap_prompter_answer)
        button.pack()

        txt_label = tk.Label(frame, text="")  # spacer
        txt_label.pack()

        subframe = tk.Frame(frame, name='extra')
        subframe.pack(side='bottom', fill='x')
        button = tk.Button(subframe, width=12, height=2, text="View @\nAnnotator",
                           command=self.view_at_annotator)
        button.pack(side='right')

    def button_click__send_to_visualobserver(self):
        self.ask_main_controller("open_VisualObserver")()
        logger.info(msg="VisualObserver opened!")
        self.send_to_visualobserver()

    def send_to_visualobserver(self):
        llm_recorder_support.send_to_visualobserver(self)

    def import_visualobserver(self):
        llm_recorder_support.import_visualobserver(self)

    def button_click__send_to_annotator(self):
        self.ask_main_controller("open_Annotator")()
        logger.info(msg="Annotator opened!")
        self.send_to_annotator()

    def send_to_annotator(self):
        llm_recorder_support.send_to_annotator(self)

    def import_annotator(self):
        llm_recorder_support.import_annotator(self)


    def button_click__send_to_caap_prompter(self):
        self.ask_main_controller("open_CAAP_prompter")()
        logger.info(msg='CAAP_prompter opened!')
        self.send_to_caap_prompter()

    def send_to_caap_prompter(self):
        llm_recorder_support.send_to_caap_prompter(self)

    def act_by_caap_prompter_answer(self):
        llm_recorder_support.act_by_caap_prompter_answer(self)

    def view_at_annotator(self):
        llm_recorder_support.view_at_annotator(self)
