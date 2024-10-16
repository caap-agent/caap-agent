import os
from src.utils.file import read_text_file


env_list_path = "./data/env_list.txt"
env_list = read_text_file(env_list_path).split('\n')

seed_list = list(range(0,100))
# In the case of click-menu-2, there were some cases where instructions were given in the form of a icon instead of natural language.
seed_list_for_click_menu_2 = [0,1,5,8,9,10,11,13,15,16,17,22,24,26,29,33,34,35,40,41,43,44,45,46,47,
48,49,50,52,53,57,58,59,60,64,67,68,70,75,77,78,79,80,81,82,83,84,86,88,89,
91,93,94,95,98,100,101,102,105,106,109,113,115,116,117,119,122,124,126,127,128,130,133,135,137,
140,142,143,144,147,148,150,151,153,156,157,161,163,165,169,171,172,174,175,176,177,178,179,188,189]
# In the case of choose-list, List excluding seeds where elements go outside the region of interest.
seed_list_for_choose_list = [0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21,
                            22, 23, 24, 25, 26, 27, 28, 29, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42,
                            43, 44, 45, 46, 48, 49, 50, 51, 52, 53, 54, 56, 57, 58, 59, 60, 61, 62, 63, 64,
                            65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 82, 83, 84, 85,
                            86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105]
# In the case of use-autocomplete, List excluding seeds where elements go outside the region of interest.
seed_list_for_use_autocomplete = [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
                                23, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 42, 44, 45, 47,
                                48, 49, 51, 52, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 69, 70, 71,
                                72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 84, 85, 86, 87, 88, 89, 90, 91, 92,
                                93, 94, 96, 97, 98, 99, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114]


# Set Demo script list
scripts_path = "./data/human_demo_scripts"
script_list = [script for script in os.listdir(scripts_path) if script.endswith('.txt')]


# The maximum number of actions has been set as we cannot allow infinite attempts for success.
default_max_action_cnt = 17
expand_max_action_cnt = 50
need_act_from_the_top_env_list = ['choose-list',]


# Set Start MiniWoB++ seed and batch size
start_idx = 0
batch_size = 50

PROJECT_LIST = []

prompt_type_list = ['BASE', 'EXCLUDE_ALL', 'EXCLUDE_PART1', 'EXCLUDE_PART2', 'EXCLUDE_PAR3']

for prompt_type in prompt_type_list:
    project = {}

    # Set GPT version
    project['GPT_version'] = '4'
    # Set FUNCTIONS version
    project['FUNCTIONS_version'] = 'func_2024_04_29__ctrlClick.json'
    # Set commentator name
    project['VISUALOBSERVER_COMMENTATOR'] = 'v1'

    project['prompt_type'] = prompt_type
    project['use_visible_element_only'] = True

    # Set Name the Test folder.
    project['name']= f"Test__{prompt_type}__{start_idx}_{start_idx+batch_size-1}"

    project['JOB_CONFIG_LIST'] = []
    JOB_CONFIG_LIST = []

    for idx in range(start_idx,start_idx+batch_size):
        for task_name in env_list:
            job_config = {}
            job_config['task'] = task_name
            job_config['seed_list'] = [seed_list[idx]]
            job_config['max_action_cnt'] = default_max_action_cnt
            if task_name in ['guess-number']:
                job_config['max_action_cnt'] = expand_max_action_cnt
            # for out of roi
            if task_name == 'choose-list':
                job_config['seed_list'] = [seed_list_for_choose_list[idx]]
            # for icon in utterance
            if task_name == 'click-menu-2':
                job_config['seed_list'] = [seed_list_for_click_menu_2[idx]]
            # for out of roi
            if task_name == 'use-autocomplete':
                job_config['seed_list'] = [seed_list_for_use_autocomplete[idx]]

            if task_name in need_act_from_the_top_env_list:
                job_config['act_from_the_top'] = True
            
            # Demo scripts are selected based on the task name.
            job_config['demo_script_file_list'] = [os.path.join(scripts_path, script) for script in script_list if script.startswith(task_name.replace('-', '_')+'_3')]
            JOB_CONFIG_LIST.append(job_config)
    project['JOB_CONFIG_LIST'] = JOB_CONFIG_LIST
    project['TESTSIZE_per_ENV'] = len(JOB_CONFIG_LIST) / len(env_list)
    PROJECT_LIST.append(project)

