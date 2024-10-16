
import win32api
import win32gui
import time
import os
import json
import pyautogui
import threading
import shutil

list_box_keyword = '!listbox'

windows_virtual_key_code_dict = {
    'A': 0x41,
    'B': 0x42,
    'C': 0x43,
    'D': 0x44,
    'E': 0x45,
    'F': 0x46,
    'G': 0x47,
    'H': 0x48,
    'I': 0x49,
    'J': 0x4A,
    'K': 0x4B,
    'L': 0x4C,
    'M': 0x4D,
    'N': 0x4E,
    'O': 0x4F,
    'P': 0x50,
    'Q': 0x51,
    'R': 0x52,
    'S': 0x53,
    'T': 0x54,
    'U': 0x55,
    'V': 0x56,
    'W': 0x57,
    'X': 0x58,
    'Y': 0x59,
    'Z': 0x5A,
    '0': 0x30,
    '1': 0x31,
    '2': 0x32,
    '3': 0x33,
    '4': 0x34,
    '5': 0x35,
    '6': 0x36,
    '7': 0x37,
    '8': 0x38,
    '9': 0x39,
    ',': 0xBC,
    '.': 0xBE,
    '/': 0xBF,
    ';': 0xBA,
    '\'': 0xDE,
    '[': 0xDB,
    ']': 0xDD,
    '\\': 0xDC,
    '-': 0xBD,
    '=': 0xBB,
    '`': 0xC0,
    ' ': 0x20
}

digit_to_upper_symbol_dict = {
    "0": ")",
    "1": "!",
    "2": "@",
    "3": "#",
    "4": "$",
    "5": "%",
    "6": "^",
    "7": "&",
    "8": "*",
    "9": "(",
}


def rec(self):
    self.record_state = "rec"

    # Reset to get utterance
    utterance = self.ask_main_controller('utterance')
    screen_region = self.ask_main_controller('miniwob_screen_region')

    action = {'name': 'start'}
    action['description'] = 'start'
    action['img'] = pyautogui.screenshot(region=screen_region)
    action['utterance'] = utterance

    self.action_list.append(action)
    self.update()

    w_handle = self.ask_main_controller('miniwob_window_handle')
    win32gui.SetForegroundWindow(w_handle)

    # Start collect_actions program in a separate thread
    thread = threading.Thread(target=collect_actions, args=(self,))
    thread.start()


def collect_actions(self):
    # Loop
    DemoRecorder = self.ask_main_controller('DemoRecorder')
    while self.record_state == "rec":
        screen_region = self.ask_main_controller('miniwob_screen_region')
        detect_point_action(self, screen_region)
        detect_type_action(self, screen_region)
        detect_mouse_down_action(self, screen_region)
        if self.FLAG__mouse_down:
            detect_more_mouse_actions(self, screen_region)
            self.FLAG__mouse_down = False

        # time.sleep(0.01)  Not really needed

        # Exit gracefully, when the window is closed while ruuning thread loop
        if DemoRecorder.win.is_closed():
            return

def detect_mouse_down_action(self, screen_region):

    win_x, win_y, win_w, win_h = screen_region

    # Left button pressed
    Left_Key = 0x01
    LB_pressed = win32api.GetKeyState(Left_Key) < 0  # Button up = 0 or 1. Button down = -127 or -128
    if LB_pressed:

        # data-1
        x, y = pyautogui.position()
        x = x - win_x
        y = y - win_y

        # Check Validity
        if (x < 0) or (x > win_w) or (y < 0) or (y > win_h):
            return

        # Check if the 'ctrl' key is pressed
        Ctrl_Key = 0x11
        ctrl_pressed = win32api.GetKeyState(Ctrl_Key) < 0

        action = {'name': 'mouse_down'}
        action['pos'] = (x, y)
        action['description'] = f"mouse_down ({x}, {y})"
        action['img'] = pyautogui.screenshot(region=screen_region)
        action['ctrl_pressed'] = ctrl_pressed

        self.FLAG__mouse_down = True
        self.action_list.append(action)
        self.update()

def detect_more_mouse_actions(self, screen_region):

    win_x, win_y, _, _ = screen_region

    Left_Key = 0x01
    Alt_Key = 0x12
    mouse_down_action = self.action_list[-1]

    # Wait until released
    alt_cnt = 0
    while True:

        # Check if the 'alt' key is pressed and released
        alt_pressed = win32api.GetKeyState(Alt_Key) < 0
        if alt_pressed:
            alt_cnt += 1

            x, y = pyautogui.position()
            x = x - win_x
            y = y - win_y

            action = {'name': 'drag_move'}
            action['pos'] = (x, y)
            action['description'] = f"drag_move ({x}, {y})"
            action['img'] = pyautogui.screenshot(region=screen_region)
            self.action_list.append(action)
            self.update()

            # Wait until released
            while True:
                released = win32api.GetKeyState(Alt_Key) >= 0
                if released:
                    break
        
        # for mouse drag action
        x, y = pyautogui.position()
        x = x - win_x
        y = y - win_y
        last_action = {'name': 'temp'}
        last_action['pos'] = (x, y)
        last_action['img'] = pyautogui.screenshot(region=screen_region)

        # Mouse is released
        released = win32api.GetKeyState(Left_Key) >= 0
        if released:
            break

    # after delay
    animation_wait_time = 0.2
    time.sleep(animation_wait_time)
    last_action['img_delayed'] = pyautogui.screenshot(region=screen_region)


    # Case: Click
    if alt_cnt == 0:
        (x1, y1) = mouse_down_action['pos']
        (x2, y2) = last_action['pos']

        DRAG_MOVEMENT_THRESHOLD = 5
        if abs(x1-x2) < DRAG_MOVEMENT_THRESHOLD and abs(y1-y2) < DRAG_MOVEMENT_THRESHOLD:

            listbox_frame = self.win.children['listbox_frame']
            listbox = listbox_frame.children[list_box_keyword]
            listbox.delete('end')  # delete the last item in the Listbox
            self.action_list = self.action_list[:-1]

            if not mouse_down_action['ctrl_pressed']:
                action = {'name': 'click'}
                action['pos1'] = mouse_down_action['pos']
                action['img1'] = mouse_down_action['img'].copy()
                action['pos2'] = last_action['pos']
                action['img2'] = last_action['img'].copy()
                action['description'] = f"click ({x1}, {y1})"
                action['img2_delayed'] = last_action['img_delayed'].copy()

            else:
                action = {'name': 'control_click'}
                action['pos1'] = mouse_down_action['pos']
                action['img1'] = mouse_down_action['img'].copy()
                action['pos2'] = last_action['pos']
                action['img2'] = last_action['img'].copy()
                action['description'] = f"control+click ({x1}, {y1})"
                action['img2_delayed'] = last_action['img_delayed'].copy()

            # update
            self.action_list.append(action)
            self.update()
            return

    # Case: When user used alt to make Drag_Move, but Mouse_Up was on same position
    # ==> ignore alt-action (delete Drag_Move action)
    if alt_cnt > 0:
        last_drag_move_action = self.action_list[-1]
        (x1, y1) = last_drag_move_action['pos']
        (x2, y2) = last_action['pos']

        DRAG_MOVEMENT_THRESHOLD = 2
        if abs(x1-x2) < DRAG_MOVEMENT_THRESHOLD and abs(y1-y2) < DRAG_MOVEMENT_THRESHOLD:

            listbox_frame = self.win.children['listbox_frame']
            listbox = listbox_frame.children[list_box_keyword]
            listbox.delete('end')  # delete the last item in the Listbox
            self.action_list = self.action_list[:-1]

    # Case: Convert mouse_up into two separate moves: drag_move + mouse_up
    action = {'name': 'drag_move'}
    action['pos'] = last_action['pos']
    action['description'] = f"drag_move ({x}, {y})"
    action['img'] = last_action['img'].copy()
    self.action_list.append(action)

    action = {'name': 'mouse_up'}
    action['description'] = "mouse_up"
    action['img'] = last_action['img'].copy()
    action['img_delayed'] = last_action['img_delayed'].copy()
    self.action_list.append(action)
    self.update()


def detect_point_action(self, screen_region):

    win_x, win_y, win_w, win_h = screen_region

    # Check if the 'alt' key is pressed
    Alt_Key = 0x12
    alt_pressed = win32api.GetKeyState(Alt_Key) < 0
    if alt_pressed:

        x, y = pyautogui.position()
        x = x - win_x
        y = y - win_y

        # Check Validity
        if (x < 0) or (x > win_w) or (y < 0) or (y > win_h):
            return

        action = {'name': 'point'}
        action['pos'] = (x, y)
        action['description'] = f"point ({x}, {y})"
        action['img'] = pyautogui.screenshot(region=screen_region)
        self.action_list.append(action)
        self.update()

        # Wait until released
        while True:
            released = win32api.GetKeyState(Alt_Key) >= 0
            if released:
                break



def detect_type_action(self, screen_region):

    FLAG__key_pressed = False
    for key, value in windows_virtual_key_code_dict.items():

        if win32api.GetKeyState(value) < 0:
            FLAG__key_pressed = True
            break

    if FLAG__key_pressed:

        control_state = win32api.GetKeyState(0x11)  # 0x11 is the virtual key code for Control
        CONTROL_flag = control_state < 0
        if CONTROL_flag and key in ['A', 'C', 'V']:
            control_key_detected(self, screen_region, key)
            return

        # modifiers
        caps_lock_state = win32api.GetKeyState(0x14)  # 0x14 is the virtual key code for Caps Lock
        CAPS_LOCK_flag = caps_lock_state == 1
        shift_key_state = win32api.GetKeyState(0x10)  # 0x10 is the virtual key code for Shift
        SHIFT_flag = shift_key_state < 0


        if key.isalpha():
            upper_used = CAPS_LOCK_flag ^ SHIFT_flag
            if upper_used:
                char = key
            else:
                char = key.lower()
        elif key.isdigit():
            if SHIFT_flag:
                char = digit_to_upper_symbol_dict[key]
            else:
                char = key
        else:
            char = key

        written = ""
        if len(self.action_list) > 0:
            previous_action = self.action_list[-1]
            if previous_action['name'] == 'type':
                written = previous_action['str']
                listbox_frame = self.win.children['listbox_frame']
                listbox = listbox_frame.children[list_box_keyword]
                listbox.delete('end')  # delete the last item in the Listbox
                self.action_list = self.action_list[:-1]

        action = {'name': 'type'}
        action['str'] = written + char
        action['description'] = f"type '{action['str']}'"

        # Wait until released
        while True:
            released = win32api.GetKeyState(value) >= 0
            if released:
                break

        # delay
        animation_wait_time = 0.2
        time.sleep(animation_wait_time)
        action['img'] = pyautogui.screenshot(region=screen_region)
        self.action_list.append(action)
        self.update()


def control_key_detected(self, screen_region, key):

    action = {'name': 'key_press'}
    if key == 'A':
        action['key_combination'] = 'Ctrl-A'
    elif key == 'C':
        action['key_combination'] = 'Ctrl-C'
    elif key == 'V':
        action['key_combination'] = 'Ctrl-V'
    action['description'] = f"key_press '{action['key_combination']}'"

    # Wait until released
    value = windows_virtual_key_code_dict[key]
    while True:
        released = win32api.GetKeyState(value) >= 0
        if released:
            break

    # no delay needed
    animation_wait_time = 0.01
    time.sleep(animation_wait_time)
    action['img'] = pyautogui.screenshot(region=screen_region)
    self.action_list.append(action)
    self.update()


def stop(self):
    self.record_state = "stop"

    if not os.path.exists(self.record_folder_path):
        os.makedirs(self.record_folder_path)

    # Save Images
    for idx, action in enumerate(self.action_list):

        if action['name'] == 'start':
            img = action['img']
            filename = f"action_{idx+1}__start.png"
            img.save(os.path.join(self.record_folder_path, filename))
            action['img'] = filename
            action['final_image'] = filename

        elif action['name'] == 'mouse_down':
            img = action['img']
            filename = f"action_{idx+1}__mouse_down.png"
            img.save(os.path.join(self.record_folder_path, filename))
            action['img'] = filename
            action['final_image'] = filename

        elif action['name'] == 'drag_move':
            img = action['img']
            filename = f"action_{idx+1}__drag_move.png"
            img.save(os.path.join(self.record_folder_path, filename))
            action['img'] = filename
            action['final_image'] = filename

        elif action['name'] == 'mouse_up':
            img = action['img']
            filename = f"action_{idx+1}__1_mouse_up.png"
            img.save(os.path.join(self.record_folder_path, filename))
            action['img'] = filename

            img = action['img_delayed']
            filename = f"action_{idx+1}__2_delayed.png"
            img.save(os.path.join(self.record_folder_path, filename))
            action['img_delayed'] = filename
            action['final_image'] = filename

        elif action['name'] == 'click':
            img = action['img1']
            filename = f"action_{idx+1}__1_mouse_down.png"
            img.save(os.path.join(self.record_folder_path, filename))
            action['img1'] = filename

            img = action['img2']
            filename = f"action_{idx+1}__2_mouse_up.png"
            img.save(os.path.join(self.record_folder_path, filename))
            action['img2'] = filename

            img = action['img2_delayed']
            filename = f"action_{idx+1}__3_delayed.png"
            img.save(os.path.join(self.record_folder_path, filename))
            action['img2_delayed'] = filename
            action['final_image'] = filename

        elif action['name'] == 'control_click':
            img = action['img1']
            filename = f"action_{idx+1}__1_mouse_down_w_control.png"
            img.save(os.path.join(self.record_folder_path, filename))
            action['img1'] = filename

            img = action['img2']
            filename = f"action_{idx+1}__2_mouse_up.png"
            img.save(os.path.join(self.record_folder_path, filename))
            action['img2'] = filename

            img = action['img2_delayed']
            filename = f"action_{idx+1}__3_delayed.png"
            img.save(os.path.join(self.record_folder_path, filename))
            action['img2_delayed'] = filename
            action['final_image'] = filename

        elif action['name'] == 'point':
            img = action['img']
            filename = f"action_{idx+1}__point.png"
            img.save(os.path.join(self.record_folder_path, filename))
            action['img'] = filename
            action['final_image'] = filename

        elif action['name'] == 'type':
            img = action['img']
            filename = f"action_{idx+1}__type_string.png"
            img.save(os.path.join(self.record_folder_path, filename))
            action['img'] = filename
            action['final_image'] = filename

        elif action['name'] == 'key_press':
            img = action['img']
            filename = f"action_{idx+1}__key_press.png"
            img.save(os.path.join(self.record_folder_path, filename))
            action['img'] = filename
            action['final_image'] = filename

        else:
            raise NotImplementedError

    # Save Dict
    json_filename = os.path.join(self.record_folder_path, "actions.json")
    with open(json_filename, "w", encoding='utf-16') as f:
        json.dump(self.action_list, f, indent=4)

    self.update()
    print(f'Saved at: {self.record_folder_path}')




def reset(self):
    self.record_state = "reset"

    # Clear Action List
    self.action_list = []
    listbox_frame = self.win.children['listbox_frame']
    listbox = listbox_frame.children[list_box_keyword]
    listbox.delete(0, 'end')

    # Clear Folder
    folder_path = self.record_folder_path
    if os.path.exists(folder_path):
        # Remove the folder and its contents
        shutil.rmtree(folder_path)

    self.update()




def update(self):

    path_text = self.win.children['savepath_frame'].children['path_text']

    if self.record_folder_path is None:
        path_text.config(text="Record Folder Not Set!")
    else:
        path_text.config(text=self.record_folder_path)

    b_frame = self.win.children['operations_frame']
    button1 = b_frame.children['rec']
    button2 = b_frame.children['stop']
    button3 = b_frame.children['reset']
    canvas = b_frame.children['canvas']
    canvas.delete("all")

    if self.record_state == None:
        button1.configure(state="disabled")
        button2.configure(state="disabled")
        button3.configure(state="disabled")
        pad = 5
        ppad = 15
        canvas.create_rectangle(0+pad, 0+ppad, 36-pad, 36-ppad, fill="black")

    elif self.record_state == 'reset':
        button1.configure(state="active")
        button2.configure(state="disabled")
        button3.configure(state="disabled")
        pad = 5
        canvas.create_oval(0+pad, 0+pad, 36-pad, 36-pad, fill="green")

    elif self.record_state == 'rec':
        button1.configure(state="disabled")
        button2.configure(state="active")
        button3.configure(state="disabled")
        pad = 5
        canvas.create_oval(0+pad, 0+pad, 36-pad, 36-pad, fill="red")

    elif self.record_state == 'stop':
        button1.configure(state="disabled")
        button2.configure(state="disabled")
        button3.configure(state="active")
        pad = 5
        canvas.create_rectangle(0+pad, 0+pad, 36-pad, 36-pad, fill="black")


    # ListBox
    listbox_frame = self.win.children['listbox_frame']
    listbox = listbox_frame.children[list_box_keyword]
    num_lines = listbox.size()
    for idx in range(len(self.action_list)):
        # skip, if written already
        if idx < num_lines:
            continue
        desc = f' action_{idx+1}: ' + self.action_list[idx]['description']
        listbox.insert('end', desc)

    # scroll to the bottom of the listbox
    listbox.yview_moveto(1.0)

    # REFRESH tkinter window displays
    self.win.update()


