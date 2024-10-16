import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Base Folder

os.environ['no_proxy'] = "182.195.92.18"

import json
import time

import tkinter as tk
from tkinter import ttk
import importlib
import win32gui
import win32con
from natsort import natsorted


from src import demo_recorder
from src import annotator

from src import demo_scripter
from src import visual_observer
from src import caap_prompter
from src import llm_recorder
from src.utils import elements_util
from src.utils import tk_window_util

from src.supports import demo_recorder_support
from src.supports import annotator_support
from src.supports import demo_scripter_support
from src.supports import visual_observer_support
from src.supports import caap_prompter_support
from src.supports import llm_recorder_support
from src.supports import main_controller_support
from src.supports import screen_commentator

import run_config

import openai


class MainController:
    def __init__(self, root):

        # Release Related
        self.data_path = "./data/"
        default_seed = 0  # 0 for test

        # Window
        self.win = root
        self.win.title("Main Controller")
        self.win.geometry("+500+200")  # will be overwritten by win_config
        self.win.geometry("380x550")  # will be overwritten by win_config
        tk_window_util.tk_window_config(self.win, self.data_path, os.path.basename(__file__))
        self.win.attributes('-topmost', True)  # Always on Top
        self.win.after_idle(self.win.attributes, '-topmost', True)  # Always on Top

        # Default GPT API VERSION
        self.GPT_API_VERSION = '4'

        # WebShop
        self.WebShop = WebShop(func=self.ask_main_controller, webshop_ip='127.0.0.1', webshop_port='3000')

        # Sub-Windows handles
        self.DemoRecorder = Temp_Sub()
        self.Annotator = Temp_Sub()
        
        self.DemoScripter = Temp_Sub()
        self.VisualObserver = Temp_Sub()
        self.CAAP_prompter = Temp_Sub()
        self.LLMRecorder = Temp_Sub()

        # ScreenCommentator 
        external_saved_checkpoint_root_path = "../../vision_model_checkpoints"
        self.screen_commentator = screen_commentator.ScreenCommentator(external_saved_checkpoint_root_path)

        # Data
        self.env_list = []  # to be updated
        self.selected_game = tk.StringVar()
        self.seed_num = tk.IntVar()
        self.seed_num.set(default_seed)

        # For Auto-Run
        self.run_result_folder = None
        self.num_run_total = 0
        self.num_run_done = 0
        self.time_run_start = None
        self.FLAG_stop_request = False
        
        self.bg_color = self.win.cget('background')

        # ETC
        self.external_env_list_path = os.path.join(self.data_path, 'env_list.txt')
        self.blank_img_path = os.path.join(self.data_path, "human_demo_record/_blank/blank_screen.png")

        # default FUNCTIONS_version
        function_json_files = natsorted([f for f in os.listdir("./functions") if f.endswith('.json')])
        assert len(function_json_files) > 0
        self.FUNCTIONS_version = function_json_files[-1]

        # Layout
        self.draw_layout()

        # Update
        self.update()

    def draw_layout(self):
        frame = tk.Frame(self.win)
        frame.pack(padx=5, pady=5, fill='x', side='bottom')
        button = tk.Button(frame, width=20, text="update",
                           command=self.update)
        button.pack()

        frame = tk.Frame(self.win, name='webshop_settings')
        frame.pack(padx=5, pady=5)
        self.fill_frame__WebShop_Settings(frame)

        frame = tk.Frame(self.win, name='webshop_human_mode')
        frame.pack(padx=5, pady=5)
        self.fill_frame__WebShop_Human_Mode(frame)

        separator = ttk.Separator(self.win, orient='horizontal')
        separator.pack(fill='x', padx=5, pady=5)

        frame = tk.Frame(self.win, name='demo_recorder_frame')
        frame.pack(padx=5, pady=5)
        self.fill_frame__Demo_Recorder(frame)

        frame = tk.Frame(self.win, name='annotator_scripter_frame')
        frame.pack(padx=5, pady=5, fill ='x')
        self.fill_frame__Annotator_Scripter(frame)

        separator = ttk.Separator(self.win, orient='horizontal')
        separator.pack(fill='x', padx=5, pady=5)

        frame = tk.Frame(self.win, name='solver')
        frame.pack(padx=5, pady=5)
        self.fill_frame__SOLVER(frame)

        frame = tk.Frame(self.win, name='llm_recorder_frame')
        frame.pack(padx=5, pady=5)
        self.fill_frame__LLM_Recorder(frame)

        separator = ttk.Separator(self.win, orient='horizontal')
        separator.pack(fill='x', padx=5, pady=5)

        frame = tk.Frame(self.win, name='run')
        frame.pack(padx=5, pady=5,fill='x')
        self.fill_frame__RUN(frame)

        frame = tk.Frame(self.win, name='empty')
        frame.pack(padx=5, pady=5, expand = True, fill ='both')

        separator = ttk.Separator(self.win, orient='horizontal')
        separator.pack(fill='x', padx=5, pady=5)

        frame = tk.Frame(self.win, name='show_and_hide')
        frame.pack(padx=5, pady=5, side='bottom', fill='x')
        self.fill_frame__show_hide(frame)

    def fill_frame__WebShop_Settings(self, frame):
        
        button = tk.Button(frame, width=30, height=2, text="Open WebShop",
                           command=self.open_WebShop)
        button.pack(side='left')

    def add_one_to_seed(self):
        self.seed_num.set(self.seed_num.get()+1)
        self.webshop_reset()

    def fill_frame__WebShop_Human_Mode(self, frame):
        # Seed Select
        txt_label = tk.Label(frame, width=5, text="Seed:", justify='left')
        txt_label.pack(side='left')
        textbox = tk.Entry(frame, width=5, textvariable=self.seed_num)
        textbox.pack(side='left')

        txt_label = tk.Label(frame, text=" ")
        txt_label.pack(side='left')

        # ADD ONE
        button = tk.Button(frame, text="+1",
                           command=self.add_one_to_seed)
        button.pack(side='left')

        button = tk.Button(frame, width=5, text="Reset",
                           command=self.webshop_reset)
        button.pack(side='left')
    
    def open_WebShop(self):
        if self.WebShop.win.is_closed():
            self.WebShop.open()
        else:
            self.WebShop.win.deiconify()

    def webshop_reset(self):
        self.WebShop.reset()

    def fill_frame__Demo_Recorder(self, frame):

        button = tk.Button(frame, width=40, height=2, text="Human Demo Recorder",
                           command=self.open_DemoRecorder)
        button.pack(side='left')

    def open_DemoRecorder(self):
        if self.DemoRecorder.win.is_closed():
            importlib.reload(demo_recorder)  # reload .py file
            importlib.reload(demo_recorder_support)  # reload .py file
            importlib.reload(elements_util)  # reload .py file
            importlib.reload(tk_window_util)
            self.DemoRecorder = demo_recorder.DemoRecorder(func=self.ask_main_controller)
        else:
            self.DemoRecorder.win.deiconify()
        self.DemoRecorder.win.focus_set()


    def fill_frame__Annotator_Scripter(self, frame):

        subframe = tk.Frame(frame, name='subframe1')
        subframe.pack(expand=True, side='left')
        button = tk.Button(subframe, width=15, height=2, text="Annotator",
                           command=self.open_Annotator)
        button.pack(side='left')
        
        subframe = tk.Frame(frame, name='subframe2')
        subframe.pack(expand=True, side='right')
        button = tk.Button(subframe, width=17, height=2, text="Demo Scripter",
                           command=self.open_DemoScripter)
        button.pack()

    def open_Annotator(self):
        if self.Annotator.win.is_closed():
            importlib.reload(annotator)  # reload .py file
            importlib.reload(annotator_support)  # reload .py file
            importlib.reload(elements_util)  # reload .py file
            importlib.reload(tk_window_util)
            self.Annotator = annotator.Annotator(func=self.ask_main_controller)
        else:
            self.Annotator.win.deiconify()
        self.Annotator.win.focus_set()


    def open_DemoScripter(self):
        if self.DemoScripter.win.is_closed():
            importlib.reload(demo_scripter)  # reload .py file
            importlib.reload(demo_scripter_support)  # reload .py file
            importlib.reload(elements_util)  # reload .py file
            importlib.reload(tk_window_util)
            self.DemoScripter = demo_scripter.DemoScripter(func=self.ask_main_controller)
        else:
            self.DemoScripter.win.deiconify()
        self.DemoScripter.win.focus_set()



    def fill_frame__SOLVER(self, frame):
        subframe = tk.Frame(frame, name='subframe1')
        subframe.pack(expand = True, fill ='x', side='left')
        button = tk.Button(subframe, width=20, height=2, text="Visual Observer",
                           command=self.open_VisualObserver)
        button.pack(side='left')

        subframe = tk.Frame(frame, name='subframe2')
        subframe.pack(expand=True, fill ='x', side='right')

        button = tk.Button(subframe, width=20, height=2, text="CAAP Prompter",
                           command=self.open_CAAP_prompter)
        button.pack()

    def open_VisualObserver(self):
        if self.VisualObserver.win.is_closed():
            importlib.reload(visual_observer)  # reload .py file
            importlib.reload(visual_observer_support)  # reload .py file
            importlib.reload(elements_util)  # reload .py file
            importlib.reload(tk_window_util)
            self.VisualObserver = visual_observer.VisualObserver(func=self.ask_main_controller)
        else:
            self.VisualObserver.win.deiconify()  # window is not visible? Must have been minimized.
        self.VisualObserver.win.focus_set()

    def open_CAAP_prompter(self):
        if self.CAAP_prompter.win.is_closed():
            importlib.reload(caap_prompter)  # reload .py file
            importlib.reload(caap_prompter_support)  # reload .py file
            importlib.reload(elements_util)  # reload .py file
            importlib.reload(tk_window_util)
            self.CAAP_prompter = caap_prompter.CAAP_prompter(func=self.ask_main_controller)
        else:
            self.CAAP_prompter.win.deiconify()
        self.CAAP_prompter.win.focus_set()


    def fill_frame__LLM_Recorder(self, frame):

        button = tk.Button(frame, width=40, height=2, text="LLM Agent Recorder",
                           command=self.open_LLMRecorder)
        button.pack(side='left')

    def open_LLMRecorder(self):
        if self.LLMRecorder.win.is_closed():
            importlib.reload(llm_recorder)  # reload .py file
            importlib.reload(llm_recorder_support)  # reload .py file
            importlib.reload(elements_util)  # reload .py file
            importlib.reload(tk_window_util)
            self.LLMRecorder = llm_recorder.LLMRecorder(func=self.ask_main_controller)
        else:
            self.LLMRecorder.win.deiconify()
        self.LLMRecorder.win.focus_set()

    def fill_frame__RUN(self, frame):

        subframe = tk.Frame(frame, name='subframe1')
        subframe.pack(padx=5, pady=5)
        button = tk.Button(subframe, width=8, height=2, text="Edit\nrun_config",
                           command=self.edit_run_config)
        button.pack(side='left')
        button = tk.Button(subframe, width=20, height=2, text="RUN", name='run_button',
                           command=self.start_run)
        button.pack(side='left')
        button = tk.Button(subframe, width=12, height=2, text="Stop", name='stop_button',
                           command=self.stop_run)
        button.pack(side='left')

        subframe = tk.Frame(frame, name='subframe2')
        subframe.pack(padx=5, pady=5)

        button = tk.Button(subframe, width=8, height=1, text="DIR",
                           command=lambda: os.startfile(os.path.abspath(self.data_path)))
        button.pack(side='left')
        txt_label = tk.Label(subframe, text="   ")
        txt_label.pack(side='left')
        txt_label = tk.Label(subframe, text="xx / xx (00 %)  PASS rate (00 %)", name='txt1')
        txt_label.pack(side='left')
        txt_label = tk.Label(subframe, text="Elapsed: NaN", name='txt2')
        txt_label.pack(side='left')

        txt_label = tk.Label(subframe, text="   ")
        txt_label.pack(side='left')
        txt_label = tk.Label(subframe, text="Avg Reward", name='avg_reward')

    def edit_run_config(self):
        filepath = os.path.join(".", "run_config.py")
        os.startfile(filepath)

    def start_run(self):
        importlib.reload(main_controller_support)
        importlib.reload(run_config)
        main_controller_support.start_run(self)

    def stop_run(self):
        self.FLAG_stop_request = True
        self.win.configure(background='black')
        self.win.after(3000, self.turn_off_stop_request)

    def turn_off_stop_request(self):
        self.FLAG_stop_request = False
        self.win.configure(background=self.bg_color)


    def fill_frame__show_hide(self, frame):

        subframe = tk.Frame(frame)
        subframe.pack(side='left', fill='x', expand=True)
        button = tk.Button(subframe, width=20, height=2, text="Show All",
                           command=self.show_all)
        button.pack()

        subframe = tk.Frame(frame)
        subframe.pack(side='left', fill='x', expand=True)
        button = tk.Button(subframe, width=20, height=2, text="Hide All",
                           command=self.hide_all)
        button.pack()

    def sub_window_lists(self):
        return [
            self.WebShop,
            self.DemoRecorder,
            self.Annotator,
            self.DemoScripter,
            self.VisualObserver,
            self.CAAP_prompter,
            self.LLMRecorder,
            ]

    def hide_all(self):
        for sub in self.sub_window_lists():
            if not sub.win.is_closed():
                sub.win.iconify()  # window is not visible? Must have been minimized.

    def show_all(self):
        for sub in self.sub_window_lists():
            if not sub.win.is_closed():
                sub.win.deiconify()  # window is not visible? Must have been minimized.


    def ask_main_controller(self, req):
        return main_controller_support.ask_main_controller(self, req)


    def update(self):
        set_environ()
        importlib.reload(main_controller_support)
        importlib.reload(elements_util)
        importlib.reload(tk_window_util)
        main_controller_support.update(self)



class fake_window:
    def __init__(self):
        self.is_closed = lambda: True

class Temp_Sub:  # used as a place-holder, so that I don't have to check if initialized or not
    def __init__(self):
        self.win = fake_window()

def enum_callback(hwnd, lparam):
        if win32gui.IsWindowEnabled(hwnd):
            if ' Task' in win32gui.GetWindowText(hwnd):
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)

def close_all_webshop_windows():
    win32gui.EnumWindows(enum_callback, None)



from PIL import Image

from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


class WebShop:
    def __init__(self, func, webshop_ip, webshop_port):
        self.REWARD_XPATH = '//*[@id="reward"]/pre'
        self.INSTRUCTION_XPATH = '//*[@id="instruction-text"]'
        self.webshop_env_ip = webshop_ip
        self.webshop_env_port = webshop_port


        self.DEFAULT_WINDOW_SIZE = 1300
        self.driver = None

        # From Master
        self.ask_main_controller = func

        self.seed_num = None
        self.utterance = None
        self.env = None
        self.observation = None
        self.info = None
        self.window_handle = None
        self.win = fake_window()

    def open(self):
        if self.driver is None:
            options = Options()
            options.add_argument("--incognito")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            self.driver = webdriver.Chrome(options)

        self.driver.set_window_size(self.DEFAULT_WINDOW_SIZE, self.DEFAULT_WINDOW_SIZE)
            

        index_id = self.ask_main_controller("seed_num")
        self.driver.get(f"http://{self.webshop_env_ip}:{self.webshop_env_port}/")
        self.driver.get(f"http://{self.webshop_env_ip}:{self.webshop_env_port}/abc_fixed__{str(index_id)}")

        self.window_handle = win32gui.GetForegroundWindow()        

        self.win.is_closed = lambda: not win32gui.IsWindow(self.window_handle)
        self.win.iconify = lambda: self.iconify()
        self.win.deiconify = lambda: self.deiconify()

        self.utterance = self.get_instruction()
    

    def reset(self):
        if self.driver:
            index_id = self.ask_main_controller("seed_num")
            self.driver.get(f"http://{self.webshop_env_ip}:{self.webshop_env_port}/")
            self.driver.get(f"http://{self.webshop_env_ip}:{self.webshop_env_port}/abc_fixed__{str(index_id)}")
            self.utterance = self.get_instruction()
        else:
            self.open()


    def iconify(self):
        win32gui.ShowWindow(self.window_handle, win32con.SW_MINIMIZE)

    def deiconify(self):
        win32gui.ShowWindow(self.window_handle, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(self.window_handle)


    def get_screenshot(self):
        image_data_bytes = self.driver.get_screenshot_as_png()
        screenshot_image = Image.open(BytesIO(image_data_bytes))
        return screenshot_image
    
    def get_reward(self):        
        reward_elements = self.driver.find_elements(By.XPATH, self.REWARD_XPATH)
        if len(reward_elements) == 0:
            return -1
        return float(reward_elements[0].text)
    
    def get_instruction(self):
        instruction_elements = self.driver.find_elements(By.XPATH, self.INSTRUCTION_XPATH)
        return instruction_elements[0].text.split('\n')[1]


def set_environ():
    """
    .credentials.json in the following format
    {
        "HTTP_PROXY": <HTTP_PROXY>,
        "HTTPS_PROXY": <HTTPS_PROXY>,
        "NO_PROXY": "",
        "REQUESTS_CA_BUNDLE": "",
        "OPENAI_API_BASE": <YOUR_OPENAPI_API_BASE>,
        "OPENAI_API_KEY": "",
        "OPENAI_API_TYPE": "azure",
        "OPENAI_API_VERSION": "2023-07-01-preview",
        "OPENAI_API_ENGINE_GPT4": "gpt-4-v1106-preview",
        "OPENAI_API_ENGINE_GPT3": "gpt-35-turbo-v1106",
    }
    """
    json_file_path = "../../.credentials.json"
    with open(json_file_path, 'r') as json_file:
        cred_json = json.load(json_file)

    for k, v in cred_json.items():
        os.environ[k] = v

    openai_env = [
        "OPENAI_API_BASE",
        "OPENAI_API_KEY",
        "OPENAI_API_TYPE",
        "OPENAI_API_VERSION",
        "OPENAI_API_ENGINE_GPT4",
        "OPENAI_API_ENGINE_GPT3",
    ]
    for k in openai_env:
        if os.environ.get(k) is None:
            raise RuntimeError(f"Environment Variable[{k}] must be set")

    openai.api_base = os.environ["OPENAI_API_BASE"]
    openai.api_key = os.environ["OPENAI_API_KEY"]
    openai.api_type = os.environ["OPENAI_API_TYPE"]
    openai.api_version = os.environ["OPENAI_API_VERSION"]


if __name__ == '__main__':
    set_environ()

    root = tk.Tk()
    MainController(root)
    root.mainloop()