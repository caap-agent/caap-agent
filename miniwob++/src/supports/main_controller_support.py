import traceback
from datetime import timedelta, datetime
import os
import time
import win32gui

import run_config

from src.utils.customexception import CustomException, ElementNotFoundError
from src.utils.file import read_text_file
# Logger
from src import get_logger
logger = get_logger(logger_name=__file__)

line_divider = "=====================\n"
def ask_main_controller(self, req):

    # MiniWob Setting
    if req == "env_name":
        env_name = self.selected_game.get()
        return env_name
    elif req == "seed_num":
        seed_num = self.seed_num.get()
        return seed_num

    # Human Mode
    elif req == "MiniWob":
        return self.Miniwob
    elif req == "miniwob_window_handle":
        return self.Miniwob.window_handle
    elif req == "miniwob_screen_region":
        win_x, win_y, _, _ = win32gui.GetWindowRect(self.Miniwob.window_handle)
        # Make sure to update the x and y offsets on each computer
        x_offset = 8
        y_offset = 32 + 43 + 8
        win_x = win_x + x_offset
        win_y = win_y + y_offset
        win_w = 160
        win_h = 50 + 160
        screen_region = (win_x, win_y, win_w, win_h)
        return screen_region
    elif req == "utterance":
        return self.Miniwob.utterance
    elif req == "reset":
        self.Miniwob.reset()
        return None
    elif req == "observation":
        return self.Miniwob.observation

    # sub windows
    elif req == "DemoRecorder":
        return self.DemoRecorder
    elif req == "Annotator":
        return self.Annotator
    elif req == "DemoScripter":
        return self.DemoScripter
    elif req == "VirtualMiniWob":
        return self.VirtualMiniWob
    elif req == "VisualObserver":
        return self.VisualObserver
    elif req == "screen_commentator":
        return self.ScreenCommentator
    elif req == "Oracle":
        return self.Prompter
        
    # screen commentator
    elif req == "ScreenCommentator":
        return self.ScreenCommentator

    # Flags
    elif req == "FLAG_stop_request":
        return self.FLAG_stop_request
    elif req == "prompt_type":
        return self.prompt_type
    elif req == "use_visible_element_only":
        return self.use_visible_element_only

    # Fuctions filename
    elif req == "FUNCTIONS_version":
        return self.FUNCTIONS_version

    # GPT API VERSION
    elif req == "GPT_API_VERSION":
        return self.GPT_API_VERSION
    # ETC
    elif req == "data_path":
        return self.data_path
    elif req == "blank_img_path":
        return self.blank_img_path

    # Window Open Functions
    elif req == "open_MiniWob":
        return self.open_MiniWob
    elif req == "open_VisualObserver":
        return self.open_VisualObserver
    elif req == "open_Annotator":
        return self.open_Annotator
    elif req == "open_CAAP_prompter":
        return self.open_CAAP_prompter


def start_run(self):
    # Open Windows
    self.open_MiniWob()
    self.open_VisualObserver()
    self.open_CAAP_prompter()
    self.open_LLMRecorder()
    PROJECT_LIST = run_config.PROJECT_LIST
    logger.info(f"projects {len(PROJECT_LIST)}")
    for project in PROJECT_LIST:
        PROJECT_NAME = project['name']
        # set gpt version 3.5 or 4.0
        self.GPT_API_VERSION = project['GPT_version']

        # exclude type for ablation test
        self.prompt_type = project['prompt_type']
        self.use_visible_element_only = project['use_visible_element_only']

        # set Fuctions filename
        self.FUNCTIONS_version = project['FUNCTIONS_version']
        # Refresh the 'Screen Commentator' model list and load a model.
        self.VisualObserver.refresh_model_list()
        self.VisualObserver.set_commentator(commentator=project['VISUALOBSERVER_COMMENTATOR'])
        self.VisualObserver.load_models()

        # Basic Info
        start_time = time.time()
        JOB_CONFIG_LIST = project['JOB_CONFIG_LIST']

        task_cnt = 0
        run_cnt = 0
        task_wo_demo_list = []
        for job_config in JOB_CONFIG_LIST:
            task_cnt += 1
            run_cnt += len(job_config['seed_list'])
            if len(job_config['demo_script_file_list']) == 0:
                task_wo_demo_list.append(job_config['task'])

        logger.info(f'Number of Tasks: {task_cnt}')
        logger.info(f'Number of Total Runs: {run_cnt}')
        if len(task_wo_demo_list) > 0:
            logger.info(f'Tasks without Demo: {len(task_wo_demo_list)}')
            for task in task_wo_demo_list:
                logger.info(f'            -(No Demo) {task}')
        
        logger.info(f"PROJECT_NAME {PROJECT_NAME} GPT_API_VERSION {self.GPT_API_VERSION}")
        # RUN
        done_cnt = 0
        count_for_pass = 0
        result_dict = {}
        txt1 = self.win.children['run'].children['subframe2'].children['txt1']
        txt2 = self.win.children['run'].children['subframe2'].children['txt2']
        txt1.config(text=f"0 / {run_cnt} (0 %)")
        self.win.update()

        result_by_env_dict = {}

        for job_config in JOB_CONFIG_LIST:
            task = job_config['task']
            get_ready_for_task(self, PROJECT_NAME, task)
            time.sleep(0.1)

            seed_list = job_config['seed_list']
            for seed in seed_list:
                try:
                    run_task(self, job_config, seed)
                    if self.FLAG_stop_request:
                        result_dict[f"{task}__seed_{seed}"] = f"JOB STATUS : {self.LLMRecorder.job_status} STOPED "
                        break
                    logger.info(seed)
                    time.sleep(1)

                    done_cnt += 1
                    if "_PASS" in self.LLMRecorder.job_status:
                        count_for_pass+=1
                        if task in result_by_env_dict:
                            result_by_env_dict[task] += 1
                        else:
                            result_by_env_dict[task] = 1
                    txt1.config(
                        text=f"{done_cnt} / {run_cnt} ({round(100 * done_cnt / run_cnt)} %)  PASS {count_for_pass} ({round(100 * count_for_pass / done_cnt)} %)")
                    time_str = str(timedelta(seconds=round(time.time() - start_time)))
                    txt2.config(text=f"Elapsed: {time_str}")
                    self.win.update()

                    result_dict[
                        f"{task}__seed_{seed}"] = f"JOB STATUS : {self.LLMRecorder.job_status} Elapsed: {time_str} "
                except Exception:
                    done_cnt += 1
                    result_dict[f"{task}__seed_{seed}"] = f"RUN TIME ERROR : {traceback.format_exc()}"
            
            if self.FLAG_stop_request:
                break

        logger.info("=====================")
        logger.info("RUN COMPLETE")
        for key, value in result_dict.items():
            logger.info(f"{key}: {value}")
        run_result_file = os.path.join(self.LLMRecorder.project_folder, f"{project['name']}_summary.txt")
        total_num = len(result_dict)
        test_size = project['TESTSIZE_per_ENV']
        if total_num > 0:
            with open(run_result_file, 'w', encoding='utf-16') as file:
                file.write(line_divider)
                file.write("RUN COMPLETE\n")
                file.write(line_divider)
                
                for key, value in result_dict.items():
                    file.write(f"{key}: {value}\n")

                file.write(
                    f"PASS : {count_for_pass}, FAIL : {total_num - count_for_pass}, Success rate : {(count_for_pass / total_num)}\n")
                file.write(line_divider)

                file.write("FULL Results by Task\n")
                for job_config in JOB_CONFIG_LIST:
                    task = job_config['task']
                    success_rate_by_env = 0.0
                    if task in result_by_env_dict:
                        success_rate_by_env = result_by_env_dict[task] / test_size
                    file.write(f"[{task}] Success Rate : {success_rate_by_env}\n")                        
                file.write(line_divider)



def get_ready_for_task(self, PROJECT_NAME, task):

    # MiniWob
    self.selected_game.set(task)
    self.miniwob_reset()

    # LLM Recorder
    project_folder = os.path.join(self.LLMRecorder.result_folder, PROJECT_NAME)
    self.LLMRecorder.load_project(project_folder)



def run_task(self, job_config, seed):

    # Ready MiniWob
    self.seed_num.set(seed)
    self.miniwob_reset()

    # Ready LLM Recorder
    self.LLMRecorder.is_invalid = False
    self.LLMRecorder.new_job()
    self.LLMRecorder.add_demo(job_config['demo_script_file_list'])

    # Select First Item in the List
    self.LLMRecorder.selected = 0
    listbox_frame = self.LLMRecorder.win.children['two_column_frame'].children['listbox_subframe']
    listbox = listbox_frame.children['!listbox']
    listbox.selection_set(self.LLMRecorder.selected)
    listbox.activate(self.LLMRecorder.selected)

    # Loop
    action_count = 0
    while self.LLMRecorder.job_status == '_INCOMPLETE':
        self.LLMRecorder.do_multi_action = False
        # Visual Observer setting
        self.LLMRecorder.send_to_visualobserver()
        self.VisualObserver.run_models()
        self.LLMRecorder.import_screen2text()

        # Stop?
        self.win.update()
        if self.FLAG_stop_request:
            return None

        if not self.LLMRecorder.do_multi_action:
            # Oracle
            self.LLMRecorder.send_to_oracle()
            self.Prompter.ask()
        # Stop?
        self.win.update()
        if self.FLAG_stop_request:
            return None

        try:
            if 'act_from_the_top' in job_config.keys() and job_config['act_from_the_top']:
                self.LLMRecorder.act_from_the_top()
            else:
                self.LLMRecorder.act_by_oracle_answer()

            action_count += 1
            if action_count == job_config['max_action_cnt']:
                self.LLMRecorder.job_status += '_MAX_ACTION_CNT'
                break
        except ElementNotFoundError as e:
            self.LLMRecorder.job_status = "_FAIL"
            action_count += 1


def update_env_list(self):
    # Get task list
    """
        Reads a task list from the given file path.
        
        Allow format
            taskname
            "taskname",
        Lines starting with '#' or '/' are ignored in the file.
    """
    if os.path.isfile(self.external_env_list_path):
        content = read_text_file(self.external_env_list_path).split('\n')
        tmp_env_list = [line.strip().replace('"', "",2).replace("'", "",2).replace(",", "") for line in content]
        self.env_list = [line for line in tmp_env_list if
                         len(line) > 0 and not (line.startswith('#') or line.startswith('/'))]

        if len(self.env_list) > 0:
            default_game = self.env_list[0]
            self.selected_game.set(default_game)
        else:
            raise CustomException("Check Environment List")


def update(self):
    update_env_list(self)

    # Miniwob Envs
    dropdown_menu = self.win.children['miniwob_settings'].children['!optionmenu']
    menu = dropdown_menu["menu"]
    menu.delete(0, "end")
    for env in self.env_list:
        menu.add_command(label=env, command=lambda value=env: self.selected_game.set(value))


