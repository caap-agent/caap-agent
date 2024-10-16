import tkinter as tk
from tkinter import ttk
import os
import sys
from PIL import Image

from src._base_window import BaseWindow
from src.supports import visual_observer_support
from src.utils.tk_window_util import tk_window_config


class Screen2Text(BaseWindow):

    def __init__(self, func):
        BaseWindow.__init__(self,
                            func=func,
                            title="Visual Observer",
                            width=700,
                            height=900,
                            support=visual_observer_support)

        # Folders
        self.conversion_folder = os.path.join("./", "DOM_conversion_rules")
        sys.path.append(self.conversion_folder)  # This is needed to import_module

        # Data
        self.selected_commentator = tk.StringVar()
        self.commentator_list = []

        self.img_original = None
        self.img_enlarged = None
        self.init_img_path = os.path.join(self.data_path, "human_demo_record/_blank/blank_screen.png")
        self.multiplier = 2  # Image Size Multiplier
        self.tk_image1 = None
        self.tk_image2 = None

        self.element_list = []
        self.element_desc_list = []

        self.client_socket = None
        self.end_of_tr_string = ''

        self.screen_commentator = self.ask_main_controller("screen_commentator")

        self.model_loaded = False
        self.selected = -1
        

        # Layout
        tk_window_config(self.win, self.data_path, os.path.basename(__file__))
        self.draw_layout()

        # Update
        self.update()

    def draw_layout(self):
        frame = tk.Frame(self.win)
        frame.pack(padx=5, pady=5, fill='x', side='bottom')
        button = tk.Button(frame, width=20, text="update", command=self.update)
        button.pack()

        frame = tk.Frame(self.win, name='load_models')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__models(frame)


        separator = ttk.Separator(self.win, orient='horizontal')
        separator.pack(fill='x', padx=5, pady=5)

        frame = tk.Frame(self.win, name='two_image_frame')
        frame.pack(padx=5, pady=5)
        self.fill_frame__two_images(frame)

        frame = tk.Frame(self.win, name='operations')
        frame.pack(fill='x', padx=5, pady=5)
        self.fill_frame__operations(frame)

        separator = ttk.Separator(self.win, orient='horizontal')
        separator.pack(fill='x', padx=5, pady=5)

        frame = tk.Frame(self.win, name='listbox_frame')
        frame.pack(padx=5, pady=5, fill='both', expand=True)
        self.fill_frame__listbox(frame)

    def fill_frame__models(self, frame):

        button = tk.Button(frame, width=8, text="refresh list",
                           command=self.refresh_model_list)
        button.pack(side='left')

        txt_label = tk.Label(frame, text="    Select Commentator:")
        txt_label.pack(side='left')
        self.selected_commentator.set('None')
        dropdown_menu = tk.OptionMenu(frame, variable=self.selected_commentator, value=['None'])
        self.selected_commentator.trace('w', self.disable_run_models_button)
        dropdown_menu.pack(side='left')
        
        button = tk.Button(frame, width=30, text="Load Models", name="load_models_button",
                           command=self.load_models)
        button.pack(side='left')


    def refresh_model_list(self):
        visual_observer_support.refresh_model_list(self, tk)

    def disable_run_models_button(self, *args):
        visual_observer_support.disable_run_models_button(self)

    def load_models(self):
        visual_observer_support.load_models(self)

    def set_commentator(self, commentator:str):
        visual_observer_support.set_commentator(self, commentator)


    def fill_frame__two_images(self, frame):
        subframe = tk.Frame(frame, name='subframe1')
        subframe.pack(fill='x', side='left')
        img_label = tk.Label(subframe, image=[], name='img1')
        img_label.pack()

        subframe = tk.Frame(frame, name='subframe2')
        subframe.pack(fill='x', side='right')
        img_label = tk.Label(subframe, image=[], name='img2')
        img_label.pack()

        # Load init image
        self.img_original = Image.open(self.init_img_path)
        self.draw_img_original()

    def draw_img_original(self):
        visual_observer_support.draw_img_original(self)


    def fill_frame__operations(self, frame):
        button = tk.Button(frame, width=10, height=2, text="Read\nAnnotator",
                           command=self.read_annotator)
        button.pack(side='left')

        subframe = tk.Frame(frame, name='subframe1')
        subframe.pack(fill='x', expand=True, side='left')
        subsub = tk.Frame(subframe, name='subsub')
        subsub.pack(side='top')
        button = tk.Button(subsub, width=24, height=2, text="Import Screen",
                           command=self.import_screen)
        button.pack(side='left')
        button = tk.Button(subsub, width=8, height=2, text="After\n3sec",
                           command=lambda: self.import_screen(delay=3))
        button.pack(side='left')

        subframe = tk.Frame(frame, name='subframe2')
        subframe.pack(fill='x', expand=True, side='right')
        subsub = tk.Frame(subframe, name='subsub')
        subsub.pack(side='top')
        button = tk.Button(subsub, width=32, height=2, text="Run Models", name='run_models_button',
                           command=self.run_models)
        button.pack(side='left')

    def read_annotator(self):
        visual_observer_support.read_annotator(self)

    def import_screen(self, delay=None):
        visual_observer_support.import_screen(self, delay)

    def run_models(self):
        visual_observer_support.run_models(self)


    def fill_frame__listbox(self, frame):

        listbox = tk.Listbox(frame, width=700, height=100)
        v_scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        h_scrollbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=listbox.xview)

        h_scrollbar.pack(side='bottom', fill=tk.X)
        v_scrollbar.pack(side='right', fill=tk.Y)
        listbox.pack(side='right', fill ='both', expand=True)

        listbox.config(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        v_scrollbar.config(command = listbox.yview)
        h_scrollbar.config(command = listbox.xview)
        listbox.bind('<<ListboxSelect>>', self.onselect)

    def onselect(self, event):
        listbox = event.widget
        selection = listbox.curselection()
        if not selection:
            self.selected = -1
        else:
            self.selected = selection[0]
        self.update()
