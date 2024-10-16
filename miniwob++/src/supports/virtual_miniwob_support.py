
import tkinter as tk
import os
import numpy as np
import win32api
import pyautogui
import re
import json

from PIL import Image, ImageTk, ImageDraw
import pandas as pd
import importlib

from src.utils.customexception import CustomException
from src.utils.file import read_text_file


def start_main_controller_task(self):

    self.demo_action_list = None
    self.demo_idx = None

    env_name = self.ask_main_controller("env_name")
    seed_num = self.ask_main_controller("seed_num")
    self.reset(env_name=env_name, seed_num=seed_num)

def start_annotator_task(self):

    Annotator = self.ask_main_controller('Annotator')
    if Annotator.win.is_closed():
        print("Annoator is NOT open!")
        return

    base_folder = os.path.basename(Annotator.demo_folder)
    match = re.match(r'^(.+?)_([0-9]+)__', base_folder)
    if match:
        task_name = match.group(1)
        seeds_digits = match.group(2)
    else:
        raise CustomException("No match found")

    json_file_path = os.path.join(Annotator.demo_folder, "actions.json")
    json_data = read_text_file(json_file_path)

    self.demo_action_list = json.loads(json_data)
    self.demo_idx = 1  # first action (idx=0) is 'start', so I ignore it.

    self.reset(env_name=task_name.replace('_', '-'), seed_num=int(seeds_digits))

def act_recorded(self):
    action = self.demo_action_list[self.demo_idx]
    action_name = action['name']

    if action_name == 'start':
        raise CustomException("This should NOT happen")

    elif action_name == 'mouse_down':
        actiontype = "MOUSEDOWN_COORDS"
        coords = np.array(list(action['pos']))
        text = None

    elif action_name == 'drag_move' or action_name == 'point':
        actiontype = "MOVE_COORDS"
        coords = np.array(list(action['pos']))
        text = None

    elif action_name == 'mouse_up':
        actiontype = "MOUSEUP_COORDS"
        coords = np.array(list(action['pos']))
        text = None

    elif action_name == 'click':
        actiontype = "CLICK_COORDS"
        coords = np.array(list(action['pos1']))
        text = None

    elif action_name == 'type':
        actiontype = "TYPE_TEXT"
        coords = None
        text = action['str']

    elif action_name == 'key_press' and action['key_combination'] == 'Ctrl-A':
        actiontype = "PRESS_KEY"
        key = 74  #"C-a"
        miniwob_action = self.env.unwrapped.create_action(actiontype, key=key)
        self.observation, _, _, _, self.info = self.env.step(miniwob_action)
        self.demo_idx += 1
        self.update()
        return

    elif action_name == 'key_press' and action['key_combination'] == 'Ctrl-C':
        actiontype = "PRESS_KEY"
        key = 75  #"C-c"
        miniwob_action = self.env.unwrapped.create_action(actiontype, key=key)
        self.observation, _, _, _, self.info = self.env.step(miniwob_action)
        self.demo_idx += 1
        self.update()
        return

    elif action_name == 'key_press' and action['key_combination'] == 'Ctrl-V':
        actiontype = "PRESS_KEY"
        key = 77  #"C-v"
        miniwob_action = self.env.unwrapped.create_action(actiontype, key=key)
        self.observation, _, _, _, self.info = self.env.step(miniwob_action)
        self.demo_idx += 1
        self.update()
        return

    elif action_name == 'control_click':
        actiontype = "CLICK_COORDS"
        key = 0x11 # control
        coords = np.array(list(action['pos1']))
        miniwob_action = self.env.unwrapped.create_action(actiontype, coords=coords, key=key)
        self.observation, _, _, _, self.info = self.env.step(miniwob_action)
        self.demo_idx += 1
        self.update()
        return

    self.step(actiontype, coords, text)
    self.demo_idx += 1
    self.update()


def get_coords_threaded(self, xvar, yvar):

    two_image_frame = self.win.children['two_image_frame']
    image_label = two_image_frame.children['subframe2'].children['img2']
    while True:
        win_x = image_label.winfo_rootx()
        win_y = image_label.winfo_rooty()
        win_w = 160 * self.multiplier
        win_h = (50 + 160) * self.multiplier
        screen_region = (win_x, win_y, win_w, win_h)

        xy = _detect_click(screen_region)
        if xy is not None:
            xvar.set(round(xy[0]/self.multiplier))
            yvar.set(round(xy[1]/self.multiplier))
            break

def _detect_click(screen_region):

    win_x, win_y, win_w, win_h = screen_region

    # Left button pressed
    Left_Key = 0x01
    LB_pressed = win32api.GetKeyState(Left_Key) < 0  # Button up = 0 or 1. Button down = -127 or -128
    if LB_pressed:
        x0, y0 = pyautogui.position()
        x0 = x0 - win_x
        y0 = y0 - win_y
        # Check Validity
        if (x0 < 0) or (x0 > win_w) or (y0 < 0) or (y0 > win_h):
            return None
        else:
            return (x0, y0)
    else:
        return None



def act(self):
    if self.action_option.get() == 1:
        actiontype = "CLICK_COORDS"
        coords = np.array([self.click_x.get(), self.click_y.get()])
        text = None

    elif self.action_option.get() == 2:
        actiontype = "TYPE_TEXT"
        coords = None
        text = self.type_string.get()

    elif self.action_option.get() == 3:
        actiontype = "MOVE_COORDS"
        coords = np.array([self.point_x.get(), self.point_y.get()])
        text = None

    elif self.action_option.get() == 4:
        actiontype = "MOUSEDOWN_COORDS"
        coords = np.array([self.drag1_x.get(), self.drag1_y.get()])
        text = None
        self.step(actiontype, coords, text)

        actiontype = "MOUSEUP_COORDS"
        coords = np.array([self.drag2_x.get(), self.drag2_y.get()])
        text = None

    elif self.action_option.get() == 11:
        actiontype = "PRESS_KEY"
        key = 74  #"C-a"  # ref: config = ActionSpaceConfig(ActionTypes.PRESS_KEY) // ActionSpaceConfig.get_preset("all_supported"), where,  from miniwob.action import Action, ActionSpaceConfig, ActionTypes
        miniwob_action = self.env.unwrapped.create_action(actiontype, key=key)
        self.observation, _, _, _, self.info = self.env.step(miniwob_action)
        self.update()
        return

    elif self.action_option.get() == 12:
        actiontype = "PRESS_KEY"
        key = 75  #"C-c"
        miniwob_action = self.env.unwrapped.create_action(actiontype, key=key)
        self.observation, _, _, _, self.info = self.env.step(miniwob_action)
        self.update()
        return

    elif self.action_option.get() == 13:
        actiontype = "PRESS_KEY"
        key = 77  #"C-v"
        miniwob_action = self.env.unwrapped.create_action(actiontype, key=key)
        self.observation, _, _, _, self.info = self.env.step(miniwob_action)
        self.update()
        return


    self.step(actiontype, coords, text)
    self.update()


def update(self):

    # Open Frame Update
    ##################################################
    txt_label = self.win.children['open'].children['counter']
    if self.demo_action_list is None:
        counter_str = "  [XXX/XXX] "
    else:
        counter_str = f"  [{self.demo_idx:03}/{len(self.demo_action_list)-1:03}] "
    txt_label.configure(text=counter_str)

    txt_label = self.win.children['open'].children['action_desc']
    if self.demo_action_list is None:
        desc = "--"
    else:
        action = self.demo_action_list[self.demo_idx]
        try:
            desc = action['description']
        except Exception:
            desc = 'no description (old record)'
    txt_label.configure(text=desc)

    button = self.win.children['open'].children['act_recorded']
    if self.demo_action_list is None:
        button.configure(state="disabled")
    elif self.demo_idx == len(self.demo_action_list)-1:
        button.configure(state="disabled")
    else:
        button.config(state="active")


    # Image Update
    ##################################################
    if self.observation is None:
        blank_img_path = self.ask_main_controller('blank_img_path')
        self.img_original = Image.open(blank_img_path)
        dom = []
    else:
        self.img_original = Image.fromarray(self.observation['screenshot'])
        dom = self.observation['dom_elements']

    # resize
    width, height = self.img_original.size
    width = width * self.multiplier
    height = height * self.multiplier
    self.img_enlarged = self.img_original.resize((width, height))

    # ROI BBOX
    image2 = self.img_enlarged.copy()
    draw = ImageDraw.Draw(image2)

    le = _get_leaf_node_list_by_tree(dom)
    for id, e in enumerate(le):
        l = e['left'][0]
        w = e['width'][0]
        t = e['top'][0]
        h = e['height'][0]

        x1 = round(l) * self.multiplier
        x2 = round(l+w) * self.multiplier
        y1 = round(t) * self.multiplier
        y2 = round(t+h) * self.multiplier

        draw.rectangle((x1, y1, x2, y2), outline='red', width=2)

    tk_image2 = ImageTk.PhotoImage(image2)
    self.tk_image2 = tk_image2

    image_frame = self.win.children['two_image_frame']
    img_label_2 = image_frame.children['subframe2'].children['img2']
    img_label_2.config(image=self.tk_image2)


    # Conversion
    ##################################################
    txt_label = self.win.children['radio_frame'].children['convert_file']
    if self.observation is None:
        convert_file = f" {self.conversion_folder}"
    else:
        module_name = self.env_name.replace("-", "_")
        convert_file = f" {self.conversion_folder}/{module_name}.py"
    txt_label.configure(text=convert_file)

    button = self.win.children['radio_frame'].children['edit_button']
    if self.observation is None:
        button.configure(state="disabled")
    else:
        button.config(state="active")

    # Data Table Update
    ##################################################
    dataframe_frame = self.win.children['dataframe_frame']
    canvas = dataframe_frame.children['!canvas']
    inner_frame = canvas.children['!frame']
    if len(le) > 0:
        df_raw = pd.DataFrame.from_records(le)
        df = df_raw[['left', 'top', 'width', 'height', 'tag', 'text', 'value']].copy()
        df['focused'] = df_raw['flags'].apply(lambda x: x[0]).copy()
        df['left'] = df['left'].apply(lambda x: x[0])
        df['top'] = df['top'].apply(lambda x: x[0])
        df['width'] = df['width'].apply(lambda x: x[0])
        df['height'] = df['height'].apply(lambda x: x[0])

        self.df_original = df.copy()

        # Conversion
        if self.df_select_option.get() == 2:

            # check if the module exist
            module_name = self.env_name.replace("-", "_")
            module_path = os.path.join(self.conversion_folder, module_name+'.py')
            if not os.path.exists(module_path):
                _create_new_conversion_file(module_path)

            module = importlib.import_module(module_name)
            importlib.reload(module)
            convert_df = getattr(module, "convert_df")
            df = convert_df(df)

        # Add index column, starting from 1
        df.reset_index(inplace=True)
        df['index'] = df['index'] + 1

        # Store
        self.df = df

        # DRAW TABLE
        ###################################################
        for widget in inner_frame.winfo_children():
            widget.destroy()

        n_rows = df.shape[0]
        n_cols = df.shape[1]

        cell_width = 13
        column_names = df.columns
        i = 0
        for j, col in enumerate(" " + column_names):
            text = tk.Text(inner_frame, width=cell_width, height=1, bg = "#9BC2E6")
            text.grid(row=i,column=j)
            text.insert('insert', col)

        # adding all the other rows into the grid
        for i in range(n_rows):
            for j in range(n_cols):
                text = tk.Text(inner_frame, width=cell_width, height=1)
                text.grid(row=i+1,column=j)
                text.insert('insert', df.iat[i, j])

        # Horizonal Scroll
        self.win.update()
        frame_w = inner_frame.winfo_width()
        frame_h = inner_frame.winfo_height()
        canvas.configure(scrollregion=(0, 0, frame_w, frame_h))


def _create_new_conversion_file(filepath):
    # create module file
    with open(filepath, "w", encoding='utf-8') as file:
        content = """from DOM_conversion_rules import convert_df_base_formatting


def convert_df(df):
    df = convert_df_base_formatting(df)

    return df
"""
        file.write(content)
    print(f"New file {filepath} has been created.")


def _get_leaf_node_list_by_tree(dom):
    num_elements = len(dom)
    parent_set = set()

    for element in dom:
        parent_set.add(element['parent'])

    leaf_elements = []
    for i in range(num_elements):
        ref = dom[i]['ref']
        if ref in parent_set:
            continue
        # if dom[i]['tag']=="div" and dom[i]['text']=="":
        #     continue
        leaf_elements.append(dom[i])

    return leaf_elements

