import win32gui
import time
import os
import json
import pyautogui
import shutil
import re
from PIL import Image

from datetime import datetime

import tkinter as tk
from tkinter import filedialog

from src.utils import elements_util
from src.utils.elements_util import ComparableElement, load_screen_history, dump_screen_history, get_sorted_elements
from src.utils.customexception import CustomException, ElementNotFoundError
from src.utils.breakdown import Breakdown
from src.utils.file import read_text_file
from src.caap_prompter import Oracle as OracleCls
# Logger
from src import get_logger
logger = get_logger(logger_name=__file__)

actions_file_name="actions.json"

def new_project(self):

    # create the popup window
    popup = tk.Toplevel()
    popup.title("New Project")
    popup.attributes("-topmost", True) # make the window appear on top of all other windows

    x_pos = self.win.winfo_x()
    y_pos = self.win.winfo_y()
    popup.geometry(f"+{x_pos}+{y_pos}")

    width = 400
    height = 200
    popup.geometry(f"{width}x{height}")

    # add a label and entry field for the folder name
    name_label = tk.Label(popup, text="New Project name:")
    name_label.pack(padx=5, pady=5)
    name_entry = tk.Entry(popup)
    name_entry.pack(padx=5, pady=5, fill='x')

    popup.name_entry = name_entry

    # create 'create' and 'cancel' buttons
    frame = tk.Frame(popup)
    frame.pack(padx=5, pady=5)
    create_button = tk.Button(frame, width=15, height=2, text="Create", command=lambda: (
        new_project_name(self, new_name=popup.name_entry.get()), popup.destroy()))

    create_button.pack(side='left', padx=5, pady=5)
    cancel_button = tk.Button(frame, width=15, height=2, text="Cancel", command=lambda: popup.destroy())
    cancel_button.pack(side='left', padx=5, pady=5)

def new_project_name(self, new_name:str):
    time_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    if new_name=="":
        project_name = f"{time_tag}"
    else:
        project_name = f"{time_tag}_{new_name}"
    self.project_folder = os.path.join(self.result_folder, project_name)
    os.makedirs(self.project_folder)

    empty_job(self)
    self.update()

def load_project(self, project_folder=None):
    if project_folder is None:
        project_folder = filedialog.askdirectory(initialdir=self.result_folder)
        if project_folder == '':
            return
    self.project_folder = project_folder
    empty_job(self)
    self.update()

def empty_job(self):
    self.job_folder = None
    self.job_seed = None
    self.job_status = None
    self.demo_folder = None
    self.demo_content_list = []
    self.action_list = []



def new_job(self):
    self.ask_main_controller('open_MiniWob')()
    logger.info(msg='MiniWob opened!')

    env_name = self.ask_main_controller("env_name")
    env_name = env_name.replace("-", "_")
    seed_num = self.ask_main_controller("seed_num")
    time_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_folder_name = f"{env_name}_{seed_num}__{time_tag}"
    self.job_folder = os.path.join(self.project_folder, job_folder_name)
    self.job_seed = seed_num
    os.makedirs(self.job_folder)
    os.makedirs(os.path.join(self.job_folder, '_INCOMPLETE'))
    self.job_status = _refresh_job_status(self)
    self.functions_folder = os.path.join(self.job_folder, self.functions_folder_name_FIXED)
    os.makedirs(self.functions_folder)
    self.demo_folder = os.path.join(self.job_folder, self.demo_folder_name_FIXED)
    os.makedirs(self.demo_folder)
    self.demo_content_list = _refresh_demo_content_list(self)

    # Actions
    self.action_list = []
    action = {}
    action['name'] = "start"
    action['script'] = "action_1: {name: start}"
    action['utterance'] = self.ask_main_controller('utterance')
    action['final_image'] = "action_1__start.png"

    self.action_list.append(action)
    _dump_action_to_json(self)

    # Annotations
    self.screen_history = []
    dump_screen_history(self.job_folder, self.action_list, -1)

    # Save Img
    w_handle = self.ask_main_controller('miniwob_window_handle')
    win32gui.SetForegroundWindow(w_handle)
    self.ask_main_controller('reset')
    time.sleep(1)

    # Set mouse initial mouse point for avoid overlap    
    screen_region = self.ask_main_controller('miniwob_screen_region')
    win_x, win_y, win_w, win_h = screen_region

    margin_space = 3
    pyautogui.moveTo(margin_space + win_x, margin_space + win_y)
    pyautogui.click(margin_space + win_x, margin_space + win_y)
    img = pyautogui.screenshot(region=screen_region)
    filename = action['final_image']
    img.save(os.path.join(self.job_folder, filename))

    # Copy Functions.   use the lastest as default
    functions_json = self.ask_main_controller('FUNCTIONS_version')

    source_file = os.path.join("./functions", functions_json)
    destination_file = os.path.join(self.functions_folder, functions_json)
    shutil.copy(source_file, destination_file)

    self.selected = -1
    self.update()


def load_job(self):

    dir_path = self.project_folder
    env_name = self.ask_main_controller("env_name")
    env_name = env_name.replace("-", "_")
    subfolders = [f for f in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, f)) and f.startswith(env_name)]

    # create the popup window
    popup = tk.Toplevel()
    popup.title("Select a Job to Load")
    popup.attributes("-topmost", True) # make the window appear on top of all other windows

    x_pos = self.win.winfo_x()
    y_pos = self.win.winfo_y()
    popup.geometry(f"+{x_pos}+{y_pos}")

    width = 400
    height = 400
    popup.geometry(f"{width}x{height}")

    frame = tk.Frame(popup)
    frame.pack(padx=5, pady=5, fill='x')
    name_label = tk.Label(frame, text="Jobs with the matching Task")
    name_label.pack(side='left', fill='x')

    frame = tk.Frame(popup, name='listbox_frame')
    frame.pack(padx=5, pady=5, fill='both', expand=True)
    listbox = tk.Listbox(frame, exportselection=False)
    v_scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
    v_scrollbar.pack(side='right', fill='y')
    listbox.pack(side='right', fill ='both', expand=True)
    listbox.config(yscrollcommand=v_scrollbar.set)
    v_scrollbar.config(command = listbox.yview)

    for item in subfolders:
        listbox.insert(tk.END, item)

    # create 'create' and 'cancel' buttons
    frame = tk.Frame(popup)
    frame.pack(padx=5, pady=5)
    create_button = tk.Button(frame, width=15, height=2, text="Load", command=lambda: load_exisitng_job(self, popup))
    create_button.pack(side='left', padx=5, pady=5)
    cancel_button = tk.Button(frame, width=15, height=2, text="Cancel", command=lambda: popup.destroy())
    cancel_button.pack(side='left', padx=5, pady=5)


def load_exisitng_job(self, popup):

    listbox = popup.children['listbox_frame'].children['!listbox']
    job_folder_name = listbox.get(listbox.curselection())
    popup.destroy()

    self.job_folder = os.path.join(self.project_folder, job_folder_name)
    _reinitialize_after_load(self)


def _reinitialize_after_load(self):
    match = re.match(r'^(.+?)_(\d+)__', os.path.basename(self.job_folder))
    if match:
        _ = match.group(1)
        seeds_digits = match.group(2)
    else:
        raise CustomException("No match found")
    self.job_seed=int(seeds_digits)
    self.job_status = _refresh_job_status(self)
    self.functions_folder = os.path.join(self.job_folder, self.functions_folder_name_FIXED)
    self.demo_folder = os.path.join(self.job_folder, self.demo_folder_name_FIXED)
    self.demo_content_list = _refresh_demo_content_list(self)
    self.action_list = _refresh_action_list(self)
    try:
        self.screen_history = load_screen_history(self.job_folder)
    except FileNotFoundError:
        for i, action in enumerate(self.action_list):
            if action.get("num_screen_elements", -1) > 0:
                dump_screen_history(self.job_folder, self.action_list, i)
        self.screen_history = load_screen_history(self.job_folder)

    self.selected = -1
    self.update()

    # focus on the last item
    listbox_frame = self.win.children['two_column_frame'].children['listbox_subframe']
    listbox = listbox_frame.children['!listbox']
    items = listbox.get(0, tk.END)
    self.selected = len(items)-1
    self.update()


def add_demo(self, file_path_tuple=None):

    if file_path_tuple == None:
        file_path_tuple = tk.filedialog.askopenfilename(initialdir='./data/human_demo_scripts',
                                                        title="Select (multiple) Demo File(s)",
                                                        multiple=True,
                                                        filetypes=(("Text files", "*.txt"),))
        if file_path_tuple == '':
            self.demo_content_list = _refresh_demo_content_list(self)
            self.update()
            return

    for path in file_path_tuple:
        filename = os.path.basename(path)
        destination_file = os.path.join(self.demo_folder, filename)
        shutil.copy(path, destination_file)

    self.demo_content_list = _refresh_demo_content_list(self)
    self.update()



def send_to_visualobserver(self):
    action_idx = round(self.selected/2 - 0.25)
    action = self.action_list[action_idx]
    img_fullpath = os.path.join(self.job_folder, action['final_image'])

    VisualObserver = self.ask_main_controller("VisualObserver")
    VisualObserver.img_original = Image.open(img_fullpath)
    VisualObserver.draw_img_original()


def import_screen2text(self):

    # Make Annotation File
    ##############################
    action_idx = round(self.selected/2 - 0.25)
    self.action_list = self.action_list[:action_idx+1]  # trim, if future actions exist
    action = self.action_list[action_idx]

    VisualObserver = self.ask_main_controller("VisualObserver")
    element_list = VisualObserver.element_list
    annotation = action['final_image'][:-3]+"json"
    annotation_fullpath = os.path.join(self.job_folder, annotation)
    with open(annotation_fullpath, 'w', encoding='utf-16') as f:
        json.dump(element_list, f, indent=4)

    # Update action
    #################################
    _update_action_list_with_imported_element_list(self)
    self.selected = self.selected + 1
    self.update()



def send_to_annotator(self):
    Annotator = self.ask_main_controller("Annotator")
    action_idx = round(self.selected/2 - 0.25)
    Annotator.load(demo_folder=self.job_folder, selected_img_idx=action_idx)


def import_annotator(self):

    # Update action
    #################################
    _update_action_list_with_imported_element_list(self)
    self.selected = self.selected + 1
    self.update()


def _update_action_list_with_imported_element_list(self):
    action_idx = round(self.selected / 2 - 0.25)
    self.action_list = self.action_list[:action_idx + 1]  # trim, if future actions exist
    action = self.action_list[action_idx]
    previous_action = self.action_list[action_idx - 1]

    if 'error' in action:
        # Just copy prev annotation
        prev_annotation = os.path.join(self.job_folder, previous_action['final_image'][:-3] + 'json')
        annotation = os.path.join(self.job_folder, action['final_image'][:-3] + 'json')
        shutil.copy(prev_annotation, annotation)

    if 'error' in action:
        for k in ['num_screen_elements', 'sub_element_list']:
            if k in previous_action:
                action[k] = previous_action[k]
    else:
        element_list = get_sorted_elements(self.job_folder, self.action_list, action_idx)
        action['num_screen_elements'] = len(element_list)

    dump_screen_history(self.job_folder, self.action_list, action_idx)
    _dump_action_to_json(self)
    _save_remained_actions(self)


def _save_remained_actions(self):
    # Read QnA
    action_idx = round(self.selected/2 - 0.25)
    required, action_queue, contents = oracle_answer_required(self, action_idx)
    if not required:
        # save remained actions
        llm_answer = contents.split(OracleCls.llm_end_write_title)[0]
        remained_actions = f"There are {len(action_queue)} remained actions:\n\n" \
                           + '\n'.join(action_queue)
        record_filename = f'QnA_{action_idx + 1}.txt'
        with open(os.path.join(self.job_folder, record_filename), 'w', encoding='utf-16') as file:
            file.write(llm_answer)
            file.write(OracleCls.llm_end_write_title)
            file.write(OracleCls.answer_write_title)
            file.write(remained_actions)


def send_to_oracle(self):
    action_idx = round(self.selected/2 - 0.25)

    Oracle = self.ask_main_controller("Oracle")
    Oracle.job_folder = self.job_folder
    Oracle.action_idx = action_idx + 1  # next action
    Oracle.generate_prompt()


def act_by_oracle_answer(self):
    # Read QnA
    action_idx = round(self.selected/2 - 0.25)
    action_queue, _ = get_action_queue(self, action_idx + 1)

    # Execute
    action_str = action_queue.pop(0)
    _execute(self, action_str)


def _execute(self, action_str):
    w_handle = self.ask_main_controller('miniwob_window_handle')
    win32gui.SetForegroundWindow(w_handle)

    match = re.findall(r"Action:\s*functions.(\w+)", action_str)
    if not match:
        logger.error(f"what action??: {action_str}")
        return _handle_error(self, None, None, None, action_str)

    reg_for_type = r'Argument:\s*\{\s*string_to_type\s*:\s*(?P<yy>.+?)\s*\}'
    reg_for_click = r'Argument:\s*\{\s*element_id\s*:\s*(?P<yy>.+?)\s*\}'
    reg_for_drag = r'Argument:\s*\{\s*x\s*:\s*(?P<xx>.+?),\s*y\s*:\s*(?P<yy>.+?)\s*\}'

    action = match[0]
    if action == "type_text":
        match = re.search(reg_for_type, action_str)
        string_to_type = match.group('yy')

        # remove quote marks
        if string_to_type.startswith("'") and string_to_type.endswith("'"):
            string_to_type = string_to_type[1:-1]
        if string_to_type.startswith('"') and string_to_type.endswith('"'):
            string_to_type = string_to_type[1:-1]

        _execute__type_text(self, string_to_type, action_name=action)

    elif action in ["press_control_A", "press_control_C", "press_control_V"]:
        _execute__short_cut(self, action_name=action)


    elif action in ["click_element", "control_click_element"]:
        match = re.search(reg_for_click, action_str)
        element_id = int(match.group('yy'))
        _execute__click_element(self, element_id, action_name=action)

    elif action == "click_new_point":
        match = re.search(reg_for_drag, action_str)
        x_loc = int(match.group('xx'))
        y_loc = int(match.group('yy'))
        _execute__click_new_point(self, x_loc, y_loc, action_name=action)

    elif action == "point_element":
        match = re.search(reg_for_click, action_str)
        element_id = int(match.group('yy'))
        _execute__point_element(self, element_id, action_name=action)

    elif action == "drag_mouse_hold_down":
        match = re.search(reg_for_drag, action_str)
        x_loc = int(match.group('xx'))
        y_loc = int(match.group('yy'))
        _execute__drag_mouse_hold_down(self, x_loc, y_loc, action_name=action)

    elif action == "drag_mouse_move":
        match = re.search(reg_for_drag, action_str)
        x_loc = int(match.group('xx'))
        y_loc = int(match.group('yy'))
        _execute__drag_mouse_move(self, x_loc, y_loc, action_name=action)

    elif action == "drag_mouse_release":
        _execute__drag_mouse_release(self, action_name=action)

    else:
        logger.error(f"what action??: {action_str}")
        return _handle_error(self, None, None, None, action_str)


def oracle_answer_required(self, action_idx):
    if action_idx <= 0:
        return True, None, None

    action_queue, contents = get_action_queue(self, action_idx)
    action_queue.pop(0)

    action = self.action_list[action_idx]
    required = 'error' in action or not action_queue or screen_changed(self, action_idx)
    return required, action_queue, contents


def get_action_queue(self, action_idx):
    # Read QnA
    record_filename = f'QnA_{action_idx}.txt'
    if self.job_folder is None:
        message = "Please check Project or Job, something invalid on LLM Recorder."
        logger.info(msg=message)
        tk.messagebox.showinfo(message=message)
        raise CustomException(message)
    contents = read_text_file(os.path.join(self.job_folder, record_filename))

    # Find action
    answer = contents.split(OracleCls.answer_write_title)[-1]

    lines = answer.split('\n')
    action_queue = {}
    for line in reversed(lines):
        match = re.search(r"Action_(?P<xx>\d+)=\(.*\)", line)
        if match:
            action_id = int(match.group('xx'))
            # Leave the latest one for each action_id and the line number must be increasing
            if not action_queue or action_id < min(action_queue.keys()):
                action_queue[action_id] = line

    # sort by action_id
    action_queue = dict(sorted(action_queue.items(), key=lambda x: x[0]))
    action_queue = list(action_queue.values())
    return action_queue, contents


def screen_changed(self, action_idx):
    if action_idx <= 0:
        return True

    prev = get_sorted_elements(self.job_folder, self.action_list, action_idx - 1)
    curr = get_sorted_elements(self.job_folder, self.action_list, action_idx)

    if len(prev) != len(curr):
        return True

    comp_prev = set(ComparableElement(e) for k, e in prev.items())
    comp_curr = set(ComparableElement(e) for k, e in curr.items())
    if comp_prev.difference(comp_curr):
        return True

    return False


def _execute__type_text(self, string_to_type, action_name: str):
    # Execute Action
    pyautogui.typewrite(string_to_type, interval=0.25)

    if not self.FLAG__disable_record:
        # Action Record
        action_idx = round(self.selected / 2 - 0.25)
        action = {'name': action_name}
        action['string_to_type'] = string_to_type
        action['script'] = f"action_{action_idx + 2}: {{name: {action_name}, arg: '{string_to_type}'}}"
        action['final_image'] = f"action_{action_idx + 2}__{action_name.lower()}.png"
        self.action_list = self.action_list[:action_idx + 1]  # trim, if future actions exist
        self.action_list.append(action)
        _dump_action_to_json(self)

        # Image Record
        __save_image(self, filename=action['final_image'])

        _check_done(self)

    self.selected = self.selected + 1
    self.update()


def __save_image(self, filename: str):
    img = _capture_screen_wo_cursor(self)
    img.save(os.path.join(self.job_folder, filename))


def _execute__short_cut(self, action_name: str):
    # Execute Action
    if action_name == "press_control_A":
        pyautogui.hotkey('ctrl', 'a')
    elif action_name == "press_control_C":
        pyautogui.hotkey('ctrl', 'c')
    elif action_name == "press_control_V":
        pyautogui.hotkey('ctrl', 'v')
    else:
        raise NotImplementedError

    if not self.FLAG__disable_record:
        # Action Record
        action_idx = round(self.selected / 2 - 0.25)
        action = {'name': action_name}
        action['script'] = f"action_{action_idx + 2}: {{name: {action_name}, arg: {{}}}}"
        action['final_image'] = f"action_{action_idx + 2}__{action_name.lower()}.png"
        self.action_list = self.action_list[:action_idx + 1]  # trim, if future actions exist
        self.action_list.append(action)
        _dump_action_to_json(self)

        # Image Record
        __save_image(self, filename=action['final_image'])

        _check_done(self)

    self.selected = self.selected + 1
    self.update()

def __extract_element(self, action_idx: int, element_id: int, action: str):
    # Execute Action
    element_list = get_sorted_elements(self.job_folder, self.action_list, action_idx, visible_only=False)
    self.element_list = element_list
    if _handle_error(self, element_id, element_list, action, None):
        return

    element = element_list[element_id]
    x, y = elements_util.get_xy_for_click(element_list, element_id)

    return element, x, y


def _execute__click_element(self, element_id: int, action_name: str):
    action_idx = round(self.selected / 2 - 0.25)
    element, x, y = __extract_element(self, action_idx=action_idx, element_id=element_id, action=action_name)

    screen_region = self.ask_main_controller('miniwob_screen_region')
    win_x, win_y, win_w, win_h = screen_region

    if action_name == 'control_click_element':
        pyautogui.keyDown('ctrl')
        pyautogui.click(x + win_x, y + win_y)
        pyautogui.keyUp('ctrl')
    elif action_name == 'click_element':
        pyautogui.click(x + win_x, y + win_y)
    else:
        raise NotImplementedError

    if not self.FLAG__disable_record:
        # Action Record
        action = {'name': action_name}
        action['element'] = json.dumps(element)
        action['script'] = f"action_{action_idx + 2}: {{name: {action_name}, arg: {elements_util.to_string(element)}}}"
        action['final_image'] = f"action_{action_idx + 2}__{action_name.lower()}.png"
        self.action_list = self.action_list[:action_idx + 1]  # trim, if future actions exist
        self.action_list.append(action)
        _dump_action_to_json(self)

        # Image Record
        __save_image(self, filename=action['final_image'])

        _check_done(self)

    self.selected = self.selected + 1
    self.update()


def _execute__click_new_point(self, x, y, action_name: str):
    # Execute Action
    screen_region = self.ask_main_controller('miniwob_screen_region')
    win_x, win_y, win_w, win_h = screen_region

    pyautogui.click(x + win_x, y + win_y)
    if not self.FLAG__disable_record:
        action_idx = round(self.selected / 2 - 0.25)

        # Action Record
        script = f"action_{action_idx + 2}: {{name: {action_name}, arg: {{x={x}, y={y}}}"
        action = {'name': action_name}
        action['xy'] = (x, y)
        action['script'] = script
        action['final_image'] = f"action_{action_idx + 2}__{action_name.lower()}.png"
        self.action_list = self.action_list[:action_idx + 1]  # trim, if future actions exist
        self.action_list.append(action)
        _dump_action_to_json(self)

        # Image Record
        __save_image(self, filename=action['final_image'])

        _check_done(self)

    self.selected = self.selected + 1
    self.update()


def _execute__point_element(self, element_id, action_name: str):
    action_idx = round(self.selected / 2 - 0.25)
    element, x, y = __extract_element(self, action_idx=action_idx, element_id=element_id, action=action_name)

    screen_region = self.ask_main_controller('miniwob_screen_region')
    win_x, win_y, win_w, win_h = screen_region

    pyautogui.moveTo(x + win_x, y + win_y)

    if not self.FLAG__disable_record:
        # Action Record
        action = {'name': action_name}
        action['element'] = json.dumps(element)
        action['script'] = f"action_{action_idx + 2}: {{name: {action_name}, arg: {elements_util.to_string(element)}}}"
        action['final_image'] = f"action_{action_idx + 2}__{action_name.lower()}.png"
        self.action_list = self.action_list[:action_idx + 1]  # trim, if future actions exist
        self.action_list.append(action)
        _dump_action_to_json(self)

        # Image Record
        __save_image(self, filename=action['final_image'])

        _check_done(self)

    self.selected = self.selected + 1
    self.update()


def _execute__drag_mouse_hold_down(self, x, y, action_name: str):
    # Execute Action
    screen_region = self.ask_main_controller('miniwob_screen_region')
    win_x, win_y, win_w, win_h = screen_region

    pyautogui.moveTo(x + win_x, y + win_y)
    pyautogui.mouseDown()

    if not self.FLAG__disable_record:
        action_idx = round(self.selected / 2 - 0.25)
        element_list = get_sorted_elements(self.job_folder, self.action_list, action_idx, visible_only=True)
        element_id = elements_util.find_by_xy(element_list, x, y)
        element = element_list.get(element_id)

        script = f"action_{action_idx + 2}: {{name: {action_name}, arg: {{x={x}, y={y}}}"
        if element:
            script += f", element: {elements_util.to_string(element)}"
        script += "}"

        # Action Record
        action = {'name': action_name}
        action['element'] = json.dumps(element)
        action['script'] = script
        action['final_image'] = f"action_{action_idx + 2}__{action_name.lower()}.png"
        self.action_list = self.action_list[:action_idx + 1]  # trim, if future actions exist
        self.action_list.append(action)
        _dump_action_to_json(self)

        # Image Record
        __save_image(self, filename=action['final_image'])

        _check_done(self)

    self.selected = self.selected + 1
    self.update()


def _execute__drag_mouse_move(self, x, y, action_name: str):
    # Execute Action
    screen_region = self.ask_main_controller('miniwob_screen_region')
    win_x, win_y, win_w, win_h = screen_region

    x_final = x + win_x
    y_final = y + win_y

    x_overshoot = x_final
    y_overshoot = y_final
    overshoot = 4

    x_undershoot = x_final
    y_undershoot = y_final
    undershoot = 1

    x_current, y_current = pyautogui.position()
    if x_current < x_final:
        x_overshoot += overshoot
    elif x_current > x_final:
        x_overshoot -= overshoot
    if y_current < y_final:
        y_overshoot += overshoot
        y_undershoot -= undershoot
    elif y_current > y_final:
        y_overshoot -= overshoot
        y_undershoot += undershoot

    pyautogui.moveTo(x_overshoot, y_overshoot, duration=0.5)
    pyautogui.moveTo(x_undershoot, y_undershoot, duration=0.1)

    if not self.FLAG__disable_record:
        x_shift = x_final - x_current
        y_shift = y_final - y_current

        # Action Record
        action_idx = round(self.selected / 2 - 0.25)
        action = {'name': action_name}
        action['xy'] = (x, y)
        action[
            'script'] = f"action_{action_idx + 2}: {{name: {action_name}, arg: {{x={x}, y={y}}}, displacement:{{x_direction={x_shift}, y_direction={y_shift}}}}}"
        action['final_image'] = f"action_{action_idx + 2}__{action_name.lower()}.png"
        self.action_list = self.action_list[:action_idx + 1]  # trim, if future actions exist
        self.action_list.append(action)
        _dump_action_to_json(self)

        # Image Record
        __save_image(self, filename=action['final_image'])

        _check_done(self)

    self.selected = self.selected + 1
    self.update()


def _execute__drag_mouse_release(self, action_name: str):
    # Execute Action
    pyautogui.mouseUp()

    if not self.FLAG__disable_record:
        # Action Record
        action_idx = round(self.selected / 2 - 0.25)
        action = {'name': action_name}
        action['script'] = f"action_{action_idx + 2}: {{name: {action_name}, arg: {{}}}}"
        action['final_image'] = f"action_{action_idx + 2}__{action_name.lower()}.png"
        self.action_list = self.action_list[:action_idx + 1]  # trim, if future actions exist
        self.action_list.append(action)
        _dump_action_to_json(self)

        # Image Record
        __save_image(self, filename=action['final_image'])

        _check_done(self)

    self.selected = self.selected + 1
    self.update()


def _execute__invalid_action(self, element_id, action_name, script, final_image_tag, error):
    action_idx = round(self.selected / 2 - 0.25)
    if not self.FLAG__disable_record:
        # Action Record
        action = {
            'name': action_name,
            'element': str(element_id),
            'script': f"action_{action_idx + 2}: {{{script}}}",
            'final_image': f"action_{action_idx + 2}__{final_image_tag}.png",
            'error': error
        }
        self.action_list = self.action_list[:action_idx + 1]  # trim, if future actions exist
        self.action_list.append(action)
        _dump_action_to_json(self)

        # Copy Image
        old_action = self.action_list[action_idx]
        old_final_img_filename_w_png = old_action['final_image']
        old_final_img_fullpath = os.path.join(self.job_folder, old_final_img_filename_w_png)
        final_img_filename_w_png = action['final_image']
        final_img_fullpath = os.path.join(self.job_folder, final_img_filename_w_png)
        shutil.copy(old_final_img_fullpath, final_img_fullpath)

    self.selected = self.selected + 1
    self.update()


def _handle_error(self, element_id, element_list, action_name, action_str):
    if action_name is None:
        script = f"received: {action_str}"
        final_image_tag = "unknown_action_error"
        error = "action is not in appropriate form to parse it or is unknown"
        _execute__invalid_action(self, element_id, action_name, script, final_image_tag, error)
        raise ElementNotFoundError(error)
    elif element_id not in element_list:
        script = f"name: {action_name}, arg: {{element_id: {element_id}}}"
        final_image_tag = "not_exist_element_error"
        error = f"element_{element_id} did not exist"
        _execute__invalid_action(self, element_id, action_name, script, final_image_tag, error)
        raise ElementNotFoundError(error)
    elif not element_list[element_id]["visible"]:
        script = f"name: {action_name}, arg: {{element_id: {element_id}}}"
        final_image_tag = "invisible_element_error"
        error = f"element_{element_id} was invisible"
        _execute__invalid_action(self, element_id, action_name, script, final_image_tag, error)
        raise ElementNotFoundError(error)
    else:
        return False


def act_from_the_top(self):

    try:
        # Miniwob Reset
        w_handle = self.ask_main_controller('miniwob_window_handle')
        win32gui.SetForegroundWindow(w_handle)
        self.ask_main_controller('reset')

        self.FLAG__disable_record = True
        target_action_idx = round(self.selected / 2 - 0.25)
        for action_idx in range(target_action_idx):
            self.selected = 2 * action_idx + 1
            self.update()
            act_by_oracle_answer(self)
            # Better Display
            self.win.update()
            time.sleep(0.5)

        # Target
        self.FLAG__disable_record = False
        self.selected = 2 * target_action_idx + 1
        self.update()
        if self.job_status == '_INCOMPLETE':
            act_by_oracle_answer(self)

    except Exception as e:
        self.FLAG__disable_record = False  # This needs to be set back to False
        self.update()
        raise e


def view_at_annotator(self):

    # Prep Folder
    files = os.listdir(self.temp_folder_path)
    for file in files:  # Loop through each file and delete it
        file_path = os.path.join(self.temp_folder_path, file)
        os.remove(file_path)

    # view_only Action
    action_idx = round(self.selected/2 - 0.25)
    view_only_action = self.action_list[action_idx].copy()
    view_only_action['name'] = 'view_only'
    view_only_action_list = [view_only_action]

    json_filename = os.path.join(self.temp_folder_path, actions_file_name)
    with open(json_filename, "w", encoding='utf-16') as f:
        json.dump(view_only_action_list, f, indent=4)

    # Image File
    img_filename = view_only_action['final_image']
    src = os.path.join(self.job_folder, img_filename)
    des = os.path.join(self.temp_folder_path, img_filename)
    shutil.copy(src, des)

    # Aannotation_file
    element_list = elements_util.get_element_list_from_annotation_file(self.job_folder, self.action_list, action_idx)
    annotation_fullpath = des[:-3] + "json"
    with open(annotation_fullpath, 'w', encoding='utf-16') as f:
        json.dump(element_list, f, indent=4)

    # Open Annotator
    self.ask_main_controller("open_Annotator")()
    logger.info(msg="Annotator opened!")
    Annotator = self.ask_main_controller("Annotator")
    Annotator.load(self.temp_folder_path)


def update(self):

    # TEXTs
    ###################################################
    name_text = self.win.children['project_name_frame'].children['project_name_text']
    name_entry = self.win.children['project_name_frame'].children['!entry']
    if self.project_folder is None:
        name_text.config(fg="red")
        name_entry.config(state="normal")
        name_entry.delete(0, tk.END)
        name_entry.insert(0, '...')
        name_entry.config(state="readonly")
    else:
        name_text.config(fg="black")
        name_entry.config(state="normal")
        name_entry.delete(0, tk.END)
        name_entry.insert(0, os.path.basename(self.project_folder))
        name_entry.config(state="readonly")

    name_text = self.win.children['job_name_frame'].children['job_name_text']
    name_entry = self.win.children['job_name_frame'].children['!entry']
    if self.job_folder is None:
        name_text.config(fg="red")
        name_entry.config(state="normal")
        name_entry.delete(0, tk.END)
        name_entry.insert(0, '...')
        name_entry.config(state="readonly")
    else:
        name_text.config(fg="black")
        name_entry.config(state="normal")
        name_entry.delete(0, tk.END)
        name_entry.insert(0, os.path.basename(self.job_folder))
        name_entry.config(state="readonly")

    seed_num = self.ask_main_controller("seed_num")
    if self.job_seed != seed_num:
        name_text.config(fg="red")
    else:
        name_text.config(fg="black")

    if self.job_folder is None:
        return

    for f in os.listdir(self.functions_folder):
        if f.endswith('.json'):
            functions_filename = f
            break
    functions_text = self.win.children['functions_frame'].children['functions_filename_text']
    functions_text.config(text=functions_filename)

    count_text = self.win.children['demo_frame'].children['demo_count_text']
    count_text.config(text=len(self.demo_content_list))


    # ListBox
    ###################################################
    listbox_frame = self.win.children['two_column_frame'].children['listbox_subframe']
    listbox = listbox_frame.children['!listbox']
    listbox.delete(0, 'end')  # delete all

    for idx, action in enumerate(self.action_list):

        desc = action['script']
        if 'error' in action:
            desc = desc[:-1] + f", error: \"{action['error']}\"" + "}"
        listbox.insert('end', ' ' + desc)

        if 'num_screen_elements' in action:
            num_el = action['num_screen_elements']
            desc = f'   └─ found elements: {num_el}'
            listbox.insert('end', desc)

    # Last Line
    self.job_status = _refresh_job_status(self)
    if self.job_status == '_PASS':
        listbox.insert('end', '   └─ Success!!')
    elif self.job_status == '_FAIL':
        listbox.insert('end', '   └─ Failed..')

    listbox.selection_set(self.selected)
    listbox.activate(self.selected)
    listbox.yview_moveto(1.0)  # scroll to the bottom of the listbox


    # Buttons
    ###################################################
    frame = self.win.children['two_column_frame'].children['operations_subframe']

    image_process_buttons_list = []
    image_process_buttons_list.append(frame.children['image_process'].children['screen2text_group'].children['!button'])
    image_process_buttons_list.append(frame.children['image_process'].children['screen2text_group'].children['!button2'])
    image_process_buttons_list.append(frame.children['image_process'].children['annotator_group'].children['!button'])
    image_process_buttons_list.append(frame.children['image_process'].children['annotator_group'].children['!button2'])

    logic_process_buttons_list = []
    logic_process_buttons_list.append(frame.children['!button'])
    logic_process_buttons_list.append(frame.children['!button2'])
    logic_process_buttons_list.append(frame.children['!button3'])
    logic_process_buttons_list.append(frame.children['extra'].children['!button'])  # view@annotator button

    if self.selected % 2 == 0:
        for button in image_process_buttons_list:
            button.configure(state="active")
        for button in logic_process_buttons_list:
            button.configure(state="disabled")
    else:
        for button in image_process_buttons_list:
            button.configure(state="disabled")
        for button in logic_process_buttons_list:
            button.configure(state="active")

        action_idx = round(self.selected / 2 - 0.25)
        if action_idx < len(self.action_list) - 1 or self.job_status not in ['_PASS', '_FAIL']:
            required, _, _ = oracle_answer_required(self, action_idx)
            if not required:
                # disable "Send to Oracle" button
                logic_process_buttons_list[0].configure(state="disabled")
                self.do_multi_action = True

    # success/fail case -- allow only the "act from the top" button
    if self.job_status in ['_PASS', '_FAIL'] and self.selected == len(self.action_list) * 2 - 2:
        for button in image_process_buttons_list:
            button.configure(state="disabled")
    if self.job_status in ['_PASS', '_FAIL'] and self.selected == len(self.action_list) * 2 - 1:
        for button in logic_process_buttons_list:
            button.configure(state="disabled")
        frame.children['!button3'].configure(state="active")


def _refresh_job_status(self):
    status_folders = []
    for f in os.listdir(self.job_folder):
        if os.path.isdir(os.path.join(self.job_folder, f)):
            if (f.startswith('_')):
                status_folders.append(f)
    if len(status_folders) != 1:
        raise CustomException("status folder not properly set")

    status = status_folders[0]
    if status not in ['_INCOMPLETE', '_PASS', '_FAIL']:
        raise CustomException(f" INVALID STAUTS : {status}")

    return status


def _refresh_demo_content_list(self):
    demo_content_list = []
    for filename in os.listdir(self.demo_folder):
        if filename.endswith(".txt"):
            demo_file = os.path.join(self.demo_folder, filename)
            demo_content = read_text_file(demo_file)
            demo_content_list.append(demo_content)

    return demo_content_list


def _refresh_action_list(self):
    # Open the JSON file and read its contents
    json_file_path = os.path.join(self.job_folder, actions_file_name)
    json_data = read_text_file(json_file_path)
    # Convert the JSON data into a dictionary object
    action_list = json.loads(json_data)
    return action_list


def _dump_action_to_json(self):
    json_filename = os.path.join(self.job_folder, actions_file_name)
    with open(json_filename, "w", encoding='utf-16') as f:
        json.dump(self.action_list, f, indent=4)


def _capture_screen_direct(self):
    time.sleep(0.1)  # maybe some animation exists. Wait a little after an action
    screen_region = self.ask_main_controller('miniwob_screen_region')
    img = pyautogui.screenshot(region=screen_region)
    return img


def _capture_screen_wo_cursor(self):
    time.sleep(0.6)  # cursor blinks out after half a second
    screen_region = self.ask_main_controller('miniwob_screen_region')
    img = pyautogui.screenshot(region=screen_region)
    return img


def _check_done(self):
    MiniWob = self.ask_main_controller('MiniWob')
    _, _, _, _, info = MiniWob.env.step(None)

    if info['done'] and info['raw_reward'] > 0:
        self.job_status = '_PASS'
    elif info['done']:
        self.job_status = '_FAIL'
    else:
        self.job_status = '_INCOMPLETE'

    for status in ['_PASS', '_FAIL', '_INCOMPLETE']:
        job_status_folder_path = os.path.join(self.job_folder, status)
        if status == self.job_status:
            if not os.path.exists(job_status_folder_path):
                os.makedirs(job_status_folder_path)
        else:
            if os.path.exists(job_status_folder_path):
                os.rmdir(job_status_folder_path)
