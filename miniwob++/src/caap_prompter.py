import tkinter as tk
from tkinter import ttk
import os

from src._base_window import BaseWindow
from src.supports import caap_prompter_support
from src.utils.tk_window_util import tk_window_config


class Oracle(BaseWindow):
    prompt_write_title = " <<<<<   PROMPT   >>>>>\n\n"
    answer_write_title = "\n\n\n <<<<<   ANSWER   >>>>>\n\n"
    llm_end_write_title = "\n\n\n <<<<<   LLM END   >>>>>\n\n"

    def __init__(self, func):
        BaseWindow.__init__(self,
                            func=func,
                            title="CAAP Prompter",
                            width=500,
                            height=500,
                            support=caap_prompter_support)

        # Folders

        # DATA
        self.action_idx = None  # for action to be made. (indexed from 0)

        self.FLAG__new_answer = False
        self.prompt = None
        self.answer = None

        self.prompt_prefix_list = ['First, ', 'Secondly, ', 'Thirdly, ', 'Fourthly, ', 'Fifthly, ', 'Sixthly, ']

        self.prompt_type = "BASE"
        self.use_visible_element_only = None

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

        frame = tk.Frame(self.win, name='job_desc_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__Job_Description(frame)

        frame = tk.Frame(self.win, name='operations_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__Operations(frame)

        separator = ttk.Separator(self.win, orient='horizontal')
        separator.pack(fill='x', padx=5, pady=5)

        frame = tk.Frame(self.win, name='functions_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__Functions(frame)


        paned_window = tk.PanedWindow(self.win, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=5)
        paned_window.pack(padx=5, fill='both', expand=True)


        frame = tk.Frame(paned_window, name='prompt_frame')
        frame.pack(fill='both')
        self.fill_frame__Prompt(frame)
        paned_window.add(frame)
        paned_window.paneconfigure(frame, height=100)
        paned_window.paneconfig(frame, minsize=40)

        frame = tk.Frame(paned_window, name='answer_frame')
        frame.pack(padx=5, pady=5, fill='both')
        self.fill_frame__Answer(frame)
        paned_window.add(frame)
        paned_window.paneconfigure(frame, height=100)
        paned_window.paneconfig(frame, minsize=40)

    def fill_frame__Job_Description(self, frame):

        txt_label = tk.Label(frame, text="For  Action #")
        txt_label.pack(side='left')

        txt_label = tk.Label(frame, text="-1", name='action_text')
        txt_label.pack(side='left')

        txt_label = tk.Label(frame, text=" of Job Name:")
        txt_label.pack(side='left')

        txt_label = tk.Label(frame, text="...", name='job_text')
        txt_label.pack(side='left')


    def fill_frame__Operations(self, frame):

        button = tk.Button(frame, width=20, height=2, text="Generate Prompt", name="gen",
                           command=self.generate_prompt)
        button.pack(side='left')

        button = tk.Button(frame, width=20, height=2, text="ASK", name="ask",
                           command=self.ask)
        button.pack(side='left')

        button = tk.Button(frame, width=20, height=2, text="Show Saved", name="show_saved",
                           command=self.show_saved)
        button.pack(side='right')

        canvas = tk.Canvas(frame, width=40, height=40, name='status_canvas')
        canvas.pack(side='right')

    def generate_prompt(self):
        caap_prompter_support.generate_prompt(self)

    def ask(self):
        caap_prompter_support.ask(self)

    def show_saved(self):
        caap_prompter_support.show_saved(self)




    def fill_frame__Functions(self, frame):

        txt_label = tk.Label(frame, text="Functions:")
        txt_label.pack(side='left')

        txt_label = tk.Label(frame, text="...", name='functions_filename_text')
        txt_label.pack(side='left')



    def fill_frame__Prompt(self, frame):
        subframe = tk.Frame(frame)
        subframe.pack(fill='x')
        txt_label = tk.Label(subframe, text="Prompt:")
        txt_label.pack(side='left')

        subframe = tk.Frame(frame, name='subframe')
        subframe.pack(fill='x', pady=5)
        text = tk.Text(subframe, height=100, name='text')
        v_scrollbar = tk.Scrollbar(subframe, orient=tk.VERTICAL, command=text.yview)
        text.config(yscrollcommand=v_scrollbar.set)
        v_scrollbar.pack(side='right', fill=tk.Y)
        text.pack(side='right', fill='both', expand=True)



    def fill_frame__Answer(self, frame):
        subframe = tk.Frame(frame)
        subframe.pack(fill='x')
        txt_label = tk.Label(subframe, text="LLM Answer:")
        txt_label.pack(side='left')

        subframe = tk.Frame(frame, name='subframe')
        subframe.pack(fill='x', pady=5)
        text = tk.Text(subframe, height=100, name='text')
        v_scrollbar = tk.Scrollbar(subframe, orient=tk.VERTICAL, command=text.yview)
        text.config(yscrollcommand=v_scrollbar.set)
        v_scrollbar.pack(side='right', fill=tk.Y)
        text.pack(side='right', fill='both', expand=True)
