
import time
import json
import os
import shutil
import threading
import queue
import traceback
import tkinter as tk
from tkinter import filedialog
import re

RETRY_ERR_MSG = r'Please retry after [0-9]+ seconds?.'

import openai

from src.utils import elements_util
from src.utils.customexception import CustomException, ElementNotFoundError
from src.utils.elements_util import dump_screen_history, get_sorted_elements
from src.utils.breakdown import Breakdown
from src.utils.file import read_text_file
# Logger
from src import get_logger
logger = get_logger(logger_name=__file__)

list_box_keyowrd = '!listbox'
message_element_not_found = 'Element Not Found!'
message_no_action_selected='No Action Selected'

def load(self):

    folder_path = filedialog.askdirectory(initialdir=self.demo_folder_path)
    if folder_path == '':
        return

    self.record_folder = folder_path

    # Open the JSON file and read its contents
    json_file_path = os.path.join(self.record_folder, "actions.json")
    json_data = read_text_file(json_file_path)
    # Convert the JSON data into a dictionary object
    original_action_list = json.loads(json_data)

    self.action_list = []
    for action in original_action_list:
        action['script'] = ''
        action['reason'] = ''

        self.action_list.append(action)

    self.update()


def view_at_annotator(self):

    # Prep Folder
    files = os.listdir(self.temp_folder_path)
    for file in files:  # Loop through each file and delete it
        file_path = os.path.join(self.temp_folder_path, file)
        os.remove(file_path)

    # view_only Action
    listbox = self.win.children['listbox_frame'].children[list_box_keyowrd]
    if not listbox.curselection():  # get selection
        print(message_no_action_selected)
        return
    sel = listbox.curselection()[0]
    view_only_action = self.action_list[sel].copy()
    view_only_action['name'] = 'view_only'
    view_only_action_list = [view_only_action]

    json_filename = os.path.join(self.temp_folder_path, "actions.json")
    with open(json_filename, "w", encoding='utf-16') as f:
        json.dump(view_only_action_list, f, indent=4)

    # Image File
    img_filename = view_only_action['final_image']
    src = os.path.join(self.record_folder, img_filename)
    des = os.path.join(self.temp_folder_path, img_filename)
    shutil.copy(src, des)

    # Aannotation_file
    element_list = elements_util.get_element_list_from_annotation_file(self.record_folder, self.action_list, sel)
    annotation_fullpath = des[:-3] + "json"
    with open(annotation_fullpath, 'w', encoding='utf-16') as f:
        json.dump(element_list, f, indent=4)

    # Open Annotator
    self.ask_main_controller("open_Annotator")()
    logger.info(msg="Annotator opened!")
    Annotator = self.ask_main_controller("Annotator")
    Annotator.load(self.temp_folder_path)


def convert(self):
    listbox = self.win.children['listbox_frame'].children[list_box_keyowrd]
    if not listbox.curselection():  # get selection
        print(message_no_action_selected)
        return
    sel = listbox.curselection()[0]
    action = self.action_list[sel]

    # Make Script
    #####################################################
    action_name = action['name']
    if sel == 0:  # start
        utterance = action["utterance"]
        script = f'''\
TASK:
{utterance}

Action History:
action_1: {{name: start}}\
'''



    elif action_name in ['type', 'key_press']:
        if action_name == 'type':
            str_content = action['str']
            script = f'action_{sel + 1}: {{name: type_text, arg: "{str_content}"}}'

        elif action_name == "key_press" and action['key_combination'] == "Ctrl-A":
            script = f"action_{sel + 1}: {{name: press_control_A, arg: {{}}}}"

        elif action_name == "key_press" and action['key_combination'] == "Ctrl-C":
            script = f"action_{sel + 1}: {{name: press_control_C, arg: {{}}}}"

        elif action_name == "key_press" and action['key_combination'] == "Ctrl-V":
            script = f"action_{sel + 1}: {{name: press_control_V, arg: {{}}}}"

    else:
        if action_name == "click":
            x, y = action['pos1']
            print(f"action {action}")
            print(f"self.action_list {self.action_list}")
            element_list = get_sorted_elements(self.record_folder, self.action_list, sel - 1)
            element_id = elements_util.find_by_xy(element_list, x, y)
            if element_id < 0:
                raise ElementNotFoundError
            element = element_list[element_id]
            element_desc = elements_util.to_string(element)
            script = f"action_{sel + 1}: {{name: click_element, arg: {element_desc}}}"

        elif action_name == "control_click":
            x, y = action['pos1']
            element_list = get_sorted_elements(self.record_folder, self.action_list, sel - 1)
            element_id = elements_util.find_by_xy(element_list, x, y)
            if element_id < 0:
                raise ElementNotFoundError
            element = element_list[element_id]
            element_desc = elements_util.to_string(element)
            script = f"action_{sel + 1}: {{name: control_click_element, arg: {element_desc}}}"

        elif action_name == "point":
            x, y = action['pos']
            element_list = get_sorted_elements(self.record_folder, self.action_list, sel - 1)
            element_id = elements_util.find_by_xy(element_list, x, y)
            if element_id < 0:
                # raise ElementNotFoundError
                script = f"action_{sel + 1}: {{name: drag_mouse_down, arg: {{x={x}, y={y}}}}}"
            else:
                element = element_list[element_id]
                element_desc = elements_util.to_string(element)
                script = f"action_{sel + 1}: {{name: point_element, arg: {{x={x}, y={y}}}, element: {element_desc}}}"

        elif action_name == "mouse_down":
            x, y = action['pos']
            element_list = get_sorted_elements(self.record_folder, self.action_list, sel - 1)
            element_id = elements_util.find_by_xy(element_list, x, y)
            if element_id < 0:
                raise ElementNotFoundError
            element = element_list[element_id]
            element_desc = elements_util.to_string(element)
            script = f"action_{sel + 1}: {{name: drag_mouse_down, arg: {{x={x}, y={y}}}, element: {element_desc}}}"

        elif action_name == "drag_move":
            x, y = action['pos']
            previous_action = self.action_list[sel - 1]
            pre_x, pre_y = previous_action['pos']
            x_shift = x - pre_x
            y_shift = y - pre_y
            script = f"action_{sel + 1}: {{name: drag_mouse_move, arg: {{x={x}, y={y}}}, displacement:{{x_direction={x_shift}, y_direction={y_shift}}}}}"

        elif action_name == "mouse_up":
            script = f"action_{sel + 1}: {{name: drag_mouse_up, arg: {{}}}}"

        else:
            raise NotImplementedError

    # Action_List Update
    #####################################################
    
    action['script'] = script
    action['reason'] = ''
    
    # Cleanup Future Actions
    for future_action in self.action_list[sel + 1:]:
        future_action['script'] = ''
        future_action['reason'] = ''

    # Update
    #####################################################
    self.update()
    if sel < len(self.action_list) - 1:
        listbox.selection_clear(0, 'end')
        listbox.selection_set(sel + 1)
        listbox.activate(sel + 1)

        # Save Screen history
        dump_screen_history(self.record_folder, self.action_list, sel)
    else:
        listbox.selection_clear(0, 'end')


def convert_to_end(self):
    listbox = self.win.children['listbox_frame'].children[list_box_keyowrd]
    try:
        sel = listbox.curselection()[0]
    except Exception:
        sel = 0
    while True:
        listbox.selection_clear(0, 'end')
        listbox.selection_set(sel)
        listbox.activate(sel)
        self.convert()
        self.win.update()
        try:
            sel = listbox.curselection()[0]
            time.sleep(0.3)  # for dramatic effect
        except Exception:
            return


def add_reason(self):
    listbox = self.win.children['listbox_frame'].children[list_box_keyowrd]
    if not listbox.curselection():  # get selection
        raise CustomException(message_no_action_selected)
    sel = listbox.curselection()[0]
    action = self.action_list[sel]

    # Write Reason
    if sel == 0:  # start
        self.answer = "Initiating the task."
    else:
        ask_for_reason(self, sel)

    action['reason'] = self.answer
    self.update()

    if sel < len(self.action_list) - 1:
        listbox.selection_clear(0, 'end')
        listbox.selection_set(sel + 1)
        listbox.activate(sel + 1)
    else:
        listbox.selection_clear(0, 'end')


def ask_for_reason(self, sel):
    self.FLAG__new_answer = False

    self.prompt = _make_prompt(self, sel)

    # run a seperate thread
    start_time = time.time()
    printed_time = 0
    result_queue = queue.Queue()
    thread = threading.Thread(target=ask_for_reason_threaded, args=(self, result_queue))
    thread.start()

    while not self.FLAG__new_answer:
        waited_time = time.time() - start_time
        if waited_time >= printed_time + 1:
            printed_time += 1
            logger.info(f"waiting for GPT answer... ({printed_time} sec)")

        time.sleep(0.01)
        self.win.update()
    logger.info("answer received")

    self.answer = result_queue.get()


def ask_for_reason_threaded(self, result_queue):

    try:
        answer = _ask_gpt_for_reason(self)

    except Exception:
        answer = traceback.format_exc()
        logger.info(answer)
        answer = "(reason omitted)"

    result_queue.put(answer)

    self.FLAG__new_answer = True


def add_reason_to_end(self):
    listbox = self.win.children['listbox_frame'].children[list_box_keyowrd]
    try:
        sel = listbox.curselection()[0]
    except Exception:
        sel = 0
    while True:
        listbox.selection_clear(0, 'end')
        listbox.selection_set(sel)
        listbox.activate(sel)
        self.add_reason()
        self.win.update()
        try:
            sel = listbox.curselection()[0]
        except Exception:
            return

def save_script(self):
    # Get the text from the listbox
    textbox = self.win.children['script_frame'].children['script_text']
    text = textbox.get("1.0", tk.END)  # get the text from the textbox

    record_foldername = os.path.basename(self.record_folder)
    demo_script_txt_filename = os.path.join(self.script_folder_path, record_foldername + ".txt")
    with open(demo_script_txt_filename, "w", encoding='utf-16') as file:
        file.write(text)  # write the text to the file

    print(f"Script is Saved: {demo_script_txt_filename}")


def update(self):

    path_text = self.win.children['path_settings_frame'].children['path_text']

    if self.record_folder is None:
        path_text.config(text="Demo Record Not Selected!")
    else:
        foldername = os.path.basename(self.record_folder)
        path_text.config(text=foldername)


    # ListBox
    listbox = self.win.children['listbox_frame'].children[list_box_keyowrd]
    if not listbox.curselection():  # get selection
        sel = None
    else:
        sel = listbox.curselection()[0]
    listbox.delete(0, 'end')  # delete all

    for idx, action in enumerate(self.action_list):
        desc = f' action_{idx + 1}: ' + self.action_list[idx]['description']
        if action['script'] == "":
            bg = '#FFDDDD'
        elif action['reason'] == "":
            bg = '#DDFFDD'
        else:
            bg = "white"

        listbox.insert('end', desc)
        listbox.itemconfig(idx, bg=bg)

    if sel is not None:
        listbox.selection_set(sel)

    # Script
    text = self.win.children['script_frame'].children['script_text']
    text.delete('1.0', tk.END)  # delete all existing text
    for action in self.action_list:
        script = action['script']
        reason = action['reason']

        if script == "":
            output = "<< EMPTY >>"
        else:
            output = script
        if reason != "":
            output = output[:-1] + f', reason: "{reason}"}}'

        text.insert(tk.END, f"{output}\n")
    # scroll to the bottom of the text
    text.yview_moveto(1.0)


def _get_screen_description(self, sel):
    FLAG__beyond_last_action = sel == len(self.action_list) - 1

    if not FLAG__beyond_last_action:
        element_list = get_sorted_elements(self.record_folder, self.action_list, sel, visible_only=False)
        desc_list = []
        for _, e in element_list.items():
            desc_list.append(f"demo_element_{e['id']}: {elements_util.to_string(e, add_visible=True)}")
        screen_description = '\n'.join(desc_list)
    else:
        screen_description = "Empty Screen (The task is completed successfully.)"

    return screen_description


def _make_prompt(self, sel):
    textbox = self.win.children['script_frame'].children['script_text']
    current_text = textbox.get("1.0", tk.END)  # get the text from the textbox

    screen_description_BEFORE = _get_screen_description(self, sel - 1)
    screen_description_AFTER = _get_screen_description(self, sel)

    # PROMPT
    ##################################################################
    prompt = f"""\
Tasks can be completed by applying appropriate actions in sequence.

Below is a record of a successful completion of the given task, demonstrated by an expert.
(Note: The trainee has added the "reason" part for each action in the record, but it may not accurately describe the reasoning used by the expert who performed the task. \
Do not assume that the written reason is correct.)

{current_text}

We want to explain to a trainee why the action_{sel + 1} was made.

Before the action_{sel + 1}, the status of the computer screen was as the following:
(Note: Coordinates are given in the form: center_x [left_edge_x-right_edge_x], center_y [top_edge_y-bottm_edge_y])
{screen_description_BEFORE}

After the action_{sel + 1}, the status of the computer screen was as the following:
{screen_description_AFTER}

First, explain how the action_{sel + 1} (both its type and its arguments) was chosen by the expert, and why it was necessary.
Since the trainee cannot view the screen, always provide a detailed description as specified whenever you refer to a screen component in your response.
Second, describe what happened after the action, as shown on the screen.

Answer in one paragraph.
"""
    logger.info(f'======  Prompt:\n\n{prompt}')

    return prompt



def _ask_gpt_for_reason(self):

    engine = os.environ['OPENAI_API_ENGINE_GPT4']

    system_content = """\
You are a helpful IT assistant. \
Your job is to help the user better understand how a task is performed on the computer screen.\
"""
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": self.prompt},
    ]

    while True:
        try:
            response = openai.ChatCompletion.create(
                engine=engine,
                messages=messages,
                functions=self.functions,
                function_call="none",
                temperature=0,
                max_tokens=2048,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None
            )

            message_received = response['choices'][0]['message']

            answer = message_received['content']
            break
        except Exception as e:
            error_msg = str(e)
            wait_msg = re.search(RETRY_ERR_MSG, error_msg)
            if wait_msg != None:
                wait_sec = int(wait_msg.group().split(' ')[3])
                time.sleep(wait_sec+1)
                continue

            answer = traceback.format_exc()
            answer += f'\n\nmessage_received = \n{message_received}'

    return answer

