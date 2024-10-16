import traceback
from datetime import timedelta
import os
import time
import win32gui
import run_config
from typing import Union

# Logger
from src import get_logger
from src.exceptions import ElementNotFoundError

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
    elif req == "WebShop":
        return self.WebShop
    elif req == "webshop_window_handle":
        return self.WebShop.window_handle
    elif req == "webshop_screen_region":
        win_x, win_y, _, _ = win32gui.GetWindowRect(self.WebShop.window_handle)
        x_offset = 8
        y_offset = 60 + 73 + 8
        win_x = win_x + x_offset
        win_y = win_y + y_offset

        webshot_offset = 1300 - self.WebShop.DEFAULT_WINDOW_SIZE
        win_w = 1284 - x_offset - webshot_offset
        win_h = 1153 - 2 - webshot_offset

        screen_region = (win_x, win_y, win_w, win_h)
        return screen_region
    elif req == "utterance":
        return self.WebShop.utterance
    elif req == "reset":
        self.WebShop.reset()
        return
    elif req == "observation":
        return self.WebShop.observation

    # sub windows
    elif req == "DemoRecorder":
        return self.DemoRecorder
    elif req == "Annotator":
        return self.Annotator
    elif req == "demo_scripter":
        return self.DemoScripter
    elif req == "VisualObserver":
        return self.VisualObserver
    elif req == "CAAP_prompter":
        return self.CAAP_prompter

    # Flags
    elif req == "FLAG_stop_request":
        return self.FLAG_stop_request    
    elif req == "use_last_reasoning":
        return self.use_last_reasoning

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
    elif req == "open_WebShop":
        return self.open_WebShop
    elif req == "open_VisualObserver":
        return self.open_VisualObserver
    elif req == "open_Annotator":
        return self.open_Annotator
    elif req == "open_CAAP_prompter":
        return self.open_CAAP_prompter
    elif req == "screen_commentator":
        return self.screen_commentator


def start_run(self):
    # Open Windows
    self.open_WebShop()
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
        self.use_last_reasoning = project['use_last_reasoning']

        # set Fuctions filename
        self.FUNCTIONS_version = project['FUNCTIONS_version']

        # Refresh the 'VisualObserver' model list and load a model.
        self.VisualObserver.refresh_model_list()
        self.VisualObserver.set_commentator(commentator=project['SCREEN2TEXT_COMMENTATOR'])
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

        logger.info(f"PROJECT_NAME {PROJECT_NAME} gpt_version {self.GPT_API_VERSION}")
        # RUN
        done_cnt = 0
        count_for_pass = 0
        reward_list = list()
        
        result_dict = {}
        txt1 = self.win.children['run'].children['subframe2'].children['txt1']
        txt2 = self.win.children['run'].children['subframe2'].children['txt2']
        txt1.config(text=f"0 / {run_cnt} (0 %)")
        self.win.update()

        # Send parquet to Server
        exp_name = project['name']
        project_abspath = os.path.abspath(os.path.join(self.VisualObserver.result_folder, PROJECT_NAME))
        
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
                        count_for_pass += 1
                        reward_list.append(self.LLMRecorder.job_reward)
                    
                    if len(reward_list) != 0:
                        txt1.config(
                            text=f"{done_cnt} / {run_cnt} ({round(100 * done_cnt / run_cnt)} %)  PASS {count_for_pass} ({round(100 * count_for_pass / done_cnt)} %) est. Task Score ({sum(reward_list)/len(reward_list)}) ")
                    else:
                        txt1.config(
                        text=f"{done_cnt} / {run_cnt} ({round(100 * done_cnt / run_cnt)} %)  PASS {count_for_pass} ({round(100 * count_for_pass / done_cnt)} %)")
                    time_str = str(timedelta(seconds=round(time.time() - start_time)))
                    txt2.config(text=f"Elapsed: {time_str}")
                    self.win.update()

                    result_dict[
                        f"{task}__seed_{seed}"] = f"JOB STATUS : {self.LLMRecorder.job_status}, Reward: {self.LLMRecorder.job_reward}, Elapsed: {time_str} "

                except Exception as e:
                    done_cnt += 1
                    result_dict[f"{task}__seed_{seed}"] = f"RUN TIME ERROR : {traceback.format_exc()}"

            if self.FLAG_stop_request:
                break
        
        logger.info("=====================")
        logger.info("RUN COMPLETE")
        for key, value in result_dict.items():
            logger.info(f"{key}: {value}")
        test_size = project['TESTSIZE_per_ENV']
        success_rate = 0.0
        if len(reward_list) == 0:
            logger.info(f"Success_rate : {success_rate}")
        else:
            success_rate = sum(reward_list) / test_size
            logger.info(f"Success_rate : {success_rate}")
        summary_file_path = os.path.join(project_abspath, f'{exp_name}_summary.txt')
        with open(summary_file_path, 'w') as f:
            f.write(line_divider)
            f.write("RUN COMPLETE\n")
            f.write(f"Task Score : {success_rate}\n")
            f.write(line_divider)
            f.write("FULL Results by Task\n")
            for key, value in result_dict.items():
                f.write(f"{key}: {value}\n")
            f.write(line_divider)

        



def get_ready_for_task(self, PROJECT_NAME, task):
    # MiniWob
    self.selected_game.set(task)
    self.webshop_reset()

    # LLM Recorder
    project_folder = os.path.join(self.LLMRecorder.result_folder, PROJECT_NAME)
    self.LLMRecorder.load_project(project_folder)


def run_task(self, job_config, seed):
    # Ready MiniWob
    self.seed_num.set(seed)
    self.webshop_reset()

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
    # try:
    while self.LLMRecorder.job_status == '_INCOMPLETE':
        self.LLMRecorder.do_multi_action = False
        # VisualObserver
        self.LLMRecorder.send_to_visualobserver()
        self.VisualObserver.run_models()
        self.LLMRecorder.import_visualobserver()

        # Stop?
        self.win.update()
        if self.FLAG_stop_request:
            return None

        if not self.LLMRecorder.do_multi_action:
            # CAAP_prompter
            self.LLMRecorder.send_to_caap_prompter()
            self.CAAP_prompter.ask()

        # Stop?
        self.win.update()
        if self.FLAG_stop_request:
            return None

        try:
            if 'act_from_the_top' in job_config.keys() and job_config['act_from_the_top']:
                self.LLMRecorder.act_from_the_top()
            else:
                self.LLMRecorder.act_by_caap_prompter_answer()

            action_count += 1
            if action_count == job_config['max_action_cnt']:
                self.LLMRecorder.job_status += '_MAX_ACTION_CNT'
                break
        except ElementNotFoundError as e:
            self.LLMRecorder.job_status = "_FAIL"
            action_count += 1


def update_env_list(self):
    self.env_list = ['webshop']
    self.selected_game.set(self.env_list[0])

def update(self):
    update_env_list(self)

