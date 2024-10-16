
import os
import json

from src.utils.file import read_text_file

def tk_window_config(root, data_path, filename):

    config_folder = os.path.join(data_path, "win_config")
    config_json_file = os.path.join(config_folder, os.path.splitext(filename)[0] + ".json")

    try:
        content = read_text_file(config_json_file)
        config = json.loads(content)
        x_pos = config['x_pos']
        y_pos = config['y_pos']
        root.geometry(f"+{x_pos}+{y_pos}")

        width = config['width']
        height = config['height']
        root.geometry(f"{width}x{height}")

    except Exception:
        # create config file
        os.makedirs(config_folder, exist_ok=True)
        with open(config_json_file, "w", encoding='utf-16') as file:
            file.write("This is a new config file.")
        print(f"New file {config_json_file} has been created.")


    # Bind the on_closing function to the window close event
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, config_json_file))
    root.is_closed = lambda: not root.winfo_exists()

    # Bring the window to FrontMost
    root.lift()



def on_closing(root, config_json_file):

    title = root.title()
    try:
        x_pos = root.winfo_x()
        y_pos = root.winfo_y()
        width = root.winfo_width()
        height = root.winfo_height()

        config = {}
        config['x_pos'] = x_pos
        config['y_pos'] = y_pos
        config['width'] = width
        config['height'] = height

        with open(config_json_file, "w", encoding='utf-16') as file:
            json.dump(config, file, indent=4)

    except Exception as e:
        print(f'Error occured while saving config file for {title}')
        print("Error:", e)

    # Destroy the window
    root.destroy()
