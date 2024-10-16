import json
import os
import queue
import threading
import tkinter as tk
import traceback
import time
import re

RETRY_ERR_MSG = r'Please retry after [0-9]+ seconds?.'

import openai

from src.utils import elements_util
from src.utils.customexception import CustomException
from src.utils.file import read_text_file
# Logger
from src import get_logger
logger = get_logger(logger_name=__file__)

def generate_prompt(self):

    self.prompt = None
    self.answer = None
    
    # Prompt
    ##########################
    intro_w_demo = _make_prompt__intro_w_demo(self)
    task_n_history = _make_prompt__task_n_history(self)
    last_reasoning = _make_prompt__last_reasoning(self)
    screen_description = _make_prompt__screen_description(self)
    direction = _make_prompt__direction(self)

    self.prompt = intro_w_demo + task_n_history + last_reasoning + screen_description + direction

    self.update()


def ask(self):

    self.FLAG__new_answer = False
    retry_count = 3
    for retry_idx in range(retry_count):
        try:
            # run a seperate thread
            start_time = time.time()
            printed_time = 0
            result_queue = queue.Queue()
            thread = threading.Thread(target=ask_threaded, args=(self, result_queue))
            thread.start()

            while not self.FLAG__new_answer:
                if self.ask_main_controller("FLAG_stop_request"):
                    logger.info("STOPPED")
                    return

                waited_time = time.time() - start_time
                if waited_time >= printed_time + 1:
                    printed_time += 1
                    logger.info(f"waiting for GPT answer... ({printed_time} sec)")

                time.sleep(0.01)
                self.win.update()
        except Exception:
            thread.join()
            self.FLAG__new_answer = False
            logger.info(f"Try count : {retry_idx + 1} , Retry for GPT answer")
        if self.FLAG__new_answer:
            break

    logger.info("answer received")

    self.answer = result_queue.get()

    # Save Answer
    record_filename = f'QnA_{self.action_idx}.txt'
    with open(os.path.join(self.job_folder, record_filename), 'w', encoding='utf-16') as file:
        file.write(self.prompt_write_title)
        file.write(self.prompt)
        file.write(self.answer_write_title)
        file.write(self.answer)
        file.write(self.llm_end_write_title)

    self.update()


def ask_threaded(self, result_queue):
    try:
        answer = _ask_gpt(self)
    except Exception:
        answer = traceback.format_exc()
    result_queue.put(answer)
    self.FLAG__new_answer = True


def show_saved(self):

    record_filename = f'QnA_{self.action_idx}.txt'
    contents = read_text_file(os.path.join(self.job_folder, record_filename))

    title1 = self.prompt_write_title
    title2 = self.answer_write_title
    title3 = self.llm_end_write_title
    title1_index = contents.find(title1)
    title2_index = contents.find(title2)
    title3_index = contents.find(title3)
    content1 = contents[title1_index + len(title1):title2_index]
    content2 = contents[title2_index + len(title2):title3_index]
    self.prompt = content1.strip()
    self.answer = content2.strip()
    self.update()



def _make_prompt__intro_w_demo(self):

    demo_content_list = []
    if self.job_folder is None:
        message = "Please check Project or Job, something invalid on LLM Recorder."
        logger.info(msg=message)
        tk.messagebox.showinfo(message=message)
        raise CustomException(message)
    demo_folder = os.path.join(self.job_folder, 'demo')
    for filename in os.listdir(demo_folder):
        if filename.endswith(".txt"):
            demo_file = os.path.join(demo_folder, filename)
            demo_content = read_text_file(demo_file)
            demo_content_list.append(demo_content)

    prompt = "Tasks can be completed by applying appropriate actions in sequence.\n\n"
    demo_paragraph = ""
    if len(demo_content_list) > 0:
        for idx, demo_content in enumerate(demo_content_list):
            text = demo_content.strip()
            lines = text.split("\n")  # Split the text into individual lines
            for i, line in enumerate(lines):
                if line.startswith("action"):
                    line = "demo_" + line
                line = (' ' * 4) + line
                lines[i] = line  # Replace the line with the modified version
            modified_text = "\n".join(lines)  # Join the lines back into a single string

            demo_paragraph += f"""\
DEMO_{idx + 1} = {{
{modified_text}
}}
"""
        prompt += f"""### Expert Demonstrations ###
For example, given below are the demos showing the correct sequence of actions for each corresponding task:
{demo_paragraph}

We are solving a similar task.
"""
    prompt += """\
You are given the history of actions made correctly by the user so far, \
and current screen status which is the result of those actions.

"""
    return prompt



def _make_prompt__task_n_history(self):

    # Open the JSON file and read its contents
    json_file_path = os.path.join(self.job_folder, "actions.json")
    json_data = read_text_file(json_file_path)
    action_list = json.loads(json_data)

    utterance = action_list[0]['utterance']

    script_list = []
    for i in range(self.action_idx):
        script = action_list[i]['script']
        script_list.append(script)
    history_content = '\n'.join(script_list)

    prompt = f"""\
### Task Description ###
{utterance}

### Action History ###
{history_content}

"""

    last_action = action_list[self.action_idx - 1]
    if 'error' in last_action:
        err_msg = f"""\
The Last Action (action_{self.action_idx}) failed because "{last_action['error']}".

"""
        prompt += err_msg

    return prompt


def _make_prompt__last_reasoning(self):
    if self.action_idx == 1:
        prompt = ""

    else:
        previous_record_filename = f'QnA_{self.action_idx - 1}.txt'
        contents = read_text_file(os.path.join(self.job_folder, previous_record_filename))

        previous_answer = contents \
            .split(self.llm_end_write_title)[0] \
            .split(self.answer_write_title)[-1] \
            .strip()

        prompt = f"""\
Reasoning behind the Last Action (action_{self.action_idx}):
'''
{previous_answer}
'''

"""
    return prompt


def _make_prompt__screen_description(self):
    self.use_visible_element_only = self.ask_main_controller("use_visible_element_only")

    all_elements = elements_util.load_screen_history(self.job_folder)
    elements = all_elements[self.action_idx - 1]

    element_description_list = []
    for _, e in elements.items():
        desc = f"- ID: element_{e['id']}, data: " + elements_util.to_string(e)
        if self.use_visible_element_only and e['visible'] is False:
            continue
        element_description_list.append(desc)

    screen_description = '\n'.join(element_description_list)

    prompt = f"""\
### The UI Element List of the Current Screen That You Can Take Next Actions On ###
(Note: Coordinates are given in the form: center_x [left_edge_x-right_edge_x], center_y [top_edge_y-bottm_edge_y])
{screen_description}

"""
    return prompt


def _make_prompt__direction(self):
    self.prompt_type = self.ask_main_controller("prompt_type").upper()

    section_number = 4
    if self.prompt_type == "EXCLUDE_ALL":
        section_number = 1

    section_sentence_dict = {1: "section", 4: "four sections"}

    intro_direction_prompt = f"""\
### Instructions ###
What should be the next actions(action_{self.action_idx + 1}, action_{self.action_idx + 2}, ...) that can be performed on the current screen?
If there is an action that can complete the task, perform it immediately. It's better if you can complete the task with fewer actions.
Your answer must be composed of the following {section_sentence_dict[section_number]}:
"""

    action_grounding_prompt = f"""\
Lastly, each action must be in the form of Action_{self.action_idx + 1}=(Action: functions.some_function_name, Argument: {{property_name: property_val}}).
Return the actions that need to be performed on the current screen.
The actions must be separated by new line characters.
In case there are three actions to be performed, your response will be in the following form:
'''
Action_{self.action_idx + 1}=(Action: functions.some_function_name, Argument: {{property_name: property_val}})
Action_{self.action_idx + 2}=(Action: functions.some_function_name, Argument: {{property_name: property_val}})
Action_{self.action_idx + 3}=(Action: functions.some_function_name, Argument: {{property_name: property_val}})
'''

- MAKE SURE that when you recommend actions that need to interact with UI elements, the UI elements MUST BE in the current screen. 
- MAKE SURE that when satisfying the task completion conditions, click the 'Submit' button to finish.
- MAKE SURE that even if you do not find a suitable action, return the most plausible one.
- MAKE SURE that since texts in elements are extracted by recognizing with OCR,  solve the given task considering that some mis-typos could exist.
"""

    prompt_part1 = f"""\
explain in detail what has been done so far up to action_{self.action_idx} and analyze why these steps were needed.
Do not assume that the user could have made a mistake.
"""
    
    prompt_part2 = f"""\
describe every single screen component that contains information that helps user solve the task or that needs to be interacted with. \
Explain about the components step by step in a detailed manner considering the given task.
When the task deals with a list of items (e.g. finding the size of a group, identifying N-th item in order, etc.), you must include the full iteration of each and every items, like this: (1)first_item, (2)second_item, ..., (N)N-th_item.
"""

    prompt_part3 = f"""\
describe what needs to be done to complete the task, detailing each action from start to finish. \
Then, identify which steps can currently be performed based on the UI elements visible on the screen, and mention the ID of these elements.
If there is a demo available, first describe the sequence of actions demonstrated, \
then link these actions to the steps in your plan before outlining the complete action plan.
"""

    direction_prompt = """"""
    if self.prompt_type == "EXCLUDE_ALL":
        action_grounding_prompt = action_grounding_prompt.replace("Lastly, e", "E")
    if self.prompt_type == "BASE":
        prompt_order = [prompt_part1, prompt_part2, prompt_part3]
    if self.prompt_type == "EXCLUDE_PART1":
        prompt_order = [prompt_part2, prompt_part3]
    if self.prompt_type == "EXCLUDE_PART2":
        prompt_order = [prompt_part2, prompt_part3]
    if self.prompt_type == "EXCLUDE_PART3":
        prompt_order = [prompt_part1, prompt_part2]
    
    for idx in range(section_number - 1):
        direction_prompt += self.prompt_prefix_list[idx] + prompt_order[idx] + '\n'

    prompt = f"""\
{intro_direction_prompt}{direction_prompt}{action_grounding_prompt}
"""

    # additional_prompt
    json_file_path = os.path.join(self.job_folder, "actions.json")
    json_data = read_text_file(json_file_path)
    action_list = json.loads(json_data)
    previous_action = action_list[self.action_idx - 1]
    if previous_action['name'] in ['drag_mouse_down', 'drag_mouse_move']:
        additional_prompt = f"""\
As we are in the middle of drag action sequence, the only valid actions are 'drag_mouse_move' and 'drag_mouse_up'."
"""
    else:
        additional_prompt = ''

    return prompt + additional_prompt


def _ask_gpt(self):

    gpt_api_version = self.ask_main_controller("GPT_API_VERSION")
    if gpt_api_version == '4':
        engine = os.environ['OPENAI_API_ENGINE_GPT4']
    elif gpt_api_version == '3':
        engine = os.environ['OPENAI_API_ENGINE_GPT3']
    else:
        engine = None

    system_content = """\
You are a helpful IT assistant. \
Your job is to help the user complete a task taking place on the computer screen.\
"""
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": self.prompt},
    ]

    functions_json = _get_functions_json(self)
    json_data = read_text_file(functions_json)
    functions = json.loads(json_data)
    invalid_response = True
    while invalid_response:
        try:
            response = openai.ChatCompletion.create(
                engine=engine,
                messages=messages,
                functions=functions,
                function_call="none",
                temperature=0,
                max_tokens=2048,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                n=1,
                seed=0
            )
            answer = response['choices'][0]['message']['content']

            invalid_response = False
        except Exception as e:
            error_msg = str(e)
            wait_msg = re.search(RETRY_ERR_MSG, error_msg)
            if wait_msg != None:
                wait_sec = int(wait_msg.group().split(' ')[3])
                time.sleep(wait_sec + 1)
                invalid_response = True
                continue

            answer = traceback.format_exc()
            message_received = response['choices'][0]['message']
            answer += f'\n\nmessage_received = \n{message_received}'

    return answer


def _get_functions_json(self):
    functions_folder = os.path.join(self.job_folder, 'functions')
    functions_list = [f for f in os.listdir(functions_folder) if f.endswith('.json')]
    functions_filename = self.ask_main_controller("FUNCTIONS_version")

    if len(functions_list) == 0 or functions_filename not in functions_list:
        raise Exception('No Functions json!')

    functions_json = os.path.join(functions_folder, functions_filename)

    return functions_json


def update(self):
    button1 = self.win.children['operations_frame'].children['gen']
    button2 = self.win.children['operations_frame'].children['ask']
    button3 = self.win.children['operations_frame'].children['show_saved']
    canvas = self.win.children['operations_frame'].children['status_canvas']
    canvas.delete("all")

    if self.job_folder is None:
        button1.configure(state="disabled")
        button2.configure(state="disabled")
        button3.configure(state="disabled")
        return

    button1.configure(state="active")
    button2.configure(state="active")

    # Check for Saved
    FLAG__Saved_File_Exist = False
    record_filename = f'QnA_{self.action_idx}.txt'
    filepath = os.path.join(self.job_folder, record_filename)
    if os.path.exists(filepath):
        FLAG__Saved_File_Exist = True

    if FLAG__Saved_File_Exist:
        button3.configure(state="active")
        canvas.create_oval(5, 5, 35, 35, fill="DodgerBlue")
    else:
        button3.configure(state="disabled")
        canvas.create_oval(5, 5, 35, 35, fill="grey")

    job_text = self.win.children['job_desc_frame'].children['job_text']
    job_text.config(text=os.path.basename(self.job_folder))
    action_text = self.win.children['job_desc_frame'].children['action_text']
    action_text.config(text=self.action_idx + 1)
    filename_text = self.win.children['functions_frame'].children['functions_filename_text']
    filename_text.configure(text=os.path.basename(_get_functions_json(self)))

    prompt_text = self.win.children['!panedwindow'].children['prompt_frame'].children['subframe'].children['text']
    prompt_text.delete('1.0', tk.END)  # delete all existing text
    if self.prompt:
        prompt_text.insert(tk.END, self.prompt)

    answer_text = self.win.children['!panedwindow'].children['answer_frame'].children['subframe'].children['text']
    answer_text.delete('1.0', tk.END)  # delete all existing text
    if self.answer:
        answer_text.insert(tk.END, self.answer)

        # scroll to the bottom of the text
        answer_text.yview_moveto(1.0)
