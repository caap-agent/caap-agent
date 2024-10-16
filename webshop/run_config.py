import os
import time

scripts_path = "./data/human_demo_scripts"
script_list = [script for script in os.listdir(scripts_path) if script.endswith('.txt')]
default_max_action_cnt = 65


task_name = 'Webshop'
now = time.localtime()


start_idx = 0
batch_size = 100

PROJECT_LIST = []
for _ in range(5):
    seed_list = list(range(start_idx,start_idx+batch_size))
    start_idx+=batch_size
    project = {}
    # Set GPT version
    project['GPT_version'] = '4'
    # Set FUNCTIONS version
    project['FUNCTIONS_version'] = 'func_2024_08_29__ctrlClick.json'
    # Set commentator name
    project['SCREEN2TEXT_COMMENTATOR'] = 'v1'
    project['use_last_reasoning'] = False
    
    local_timestamp = f"{str(now.tm_year)[2:]}{now.tm_mon:02d}{now.tm_mday:02d}{now.tm_hour:02d}{now.tm_min:02d}{now.tm_sec:02d}"
    project['name']= f"WS_Test_part_{len(PROJECT_LIST)}_{local_timestamp}__{seed_list[0]}_to_{seed_list[-1]}"

    project['JOB_CONFIG_LIST'] = []
    JOB_CONFIG_LIST = []

    for idx in seed_list:
        job_config = {}
        job_config['task'] = task_name
        job_config['seed_list'] = [idx]
        job_config['max_action_cnt'] = default_max_action_cnt

        job_config['demo_script_file_list'] = [os.path.join(scripts_path, script) for script in script_list if (script).upper().startswith(task_name.upper().replace('-', '_'))]

        JOB_CONFIG_LIST.append(job_config)
    project['JOB_CONFIG_LIST'] = JOB_CONFIG_LIST
    project['TESTSIZE_per_ENV'] = len(seed_list)
    PROJECT_LIST.append(project)