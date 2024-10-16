import os
import json
import copy
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw, ImageChops, ImageStat

from src.utils import elements_util
from src.utils.file import read_text_file

TYPE_DICT = elements_util.TYPE_DICT
DICT_TYPE = {v: k for k, v in TYPE_DICT.items()}  # converted TYPE_DICT
KEYS_USED = elements_util.KEYS_USED
SUBTYPE_OPTIONS = elements_util.SUBTYPE_OPTIONS


def _get_refreshed_demo_folder(self):
    demo_folder_list = []
    for dir_name in os.listdir(self.demo_folder_base):
        fullpath = os.path.join(self.demo_folder_base, dir_name)
        if os.path.isdir(fullpath):
            demo_folder_list.append(fullpath)
    demo_folder_list.sort()

    if len(demo_folder_list) == 0:
        demo_idx = -1
    else:
        base_name = os.path.basename(self.demo_folder)

        demo_idx = [idx for idx, data in enumerate(demo_folder_list) if base_name in data][0]

    return demo_folder_list, demo_idx


def load(self, demo_folder=None, selected_img_idx=0):
    if demo_folder is None:
        demo_folder = filedialog.askdirectory(initialdir=self.demo_folder_base)
        if demo_folder == '':
            return

    self.demo_folder = demo_folder
    self.demo_folder_base = os.path.dirname(self.demo_folder)
    self.demo_folder_list, self.demo_idx = _get_refreshed_demo_folder(self)

    # Make the list
    # Open the JSON file and read its contents
    json_file_path = os.path.join(self.demo_folder, "actions.json")
    json_data = read_text_file(json_file_path)
    # Convert the JSON data into a dictionary object
    self.action_list = json.loads(json_data)

    # Remove last action, if it ends with a blank image
    blank_img_path = self.ask_main_controller('blank_img_path')
    img_blank = Image.open(blank_img_path)
    last_final_image_path = os.path.join(self.demo_folder, self.action_list[-1]['final_image'])
    last_final_image = Image.open(last_final_image_path)
    diff = ImageChops.difference(last_final_image, img_blank)
    average_value = ImageStat.Stat(diff).mean
    average = sum(average_value) / len(average_value)
    if average < 2:  # rough threshold --- True, if DONE
        self.action_list = self.action_list[:-1]

    # Fill in Lists
    self.image_list = []
    for action in self.action_list:
        self.image_list.append(action['final_image'])

    self.annotation_list = []
    for image_file_name_w_png in self.image_list:
        annotation = image_file_name_w_png[:-3] + "json"
        self.annotation_list.append(annotation)

        annotation_fullpath = os.path.join(self.demo_folder, annotation)
        if not os.path.exists(annotation_fullpath):
            element_list = []
            with open(annotation_fullpath, 'w', encoding='utf-16') as f:
                json.dump(element_list, f)

    load_image(self, selected_img_idx)


def get_prev_dir(self):
    self.demo_folder_list, self.demo_idx = _get_refreshed_demo_folder(self)
    if len(self.demo_folder_list) == 0:
        return
    if self.demo_idx < 0:
        return
    self.demo_idx = max(self.demo_idx - 1, 0)
    load(self, self.demo_folder_list[self.demo_idx])


def get_next_dir(self):
    self.demo_folder_list, self.demo_idx = _get_refreshed_demo_folder(self)
    if len(self.demo_folder_list) == 0:
        return
    if self.demo_idx < 0:
        return
    self.demo_idx = min(self.demo_idx + 1, len(self.demo_folder_list) - 1)
    load(self, self.demo_folder_list[self.demo_idx])


def prev_image(self):
    if self.selected_img_idx <= 0:
        return
    saved_selected_idx = self.selected
    load_image(self, self.selected_img_idx - 1)

    if len(self.element_list) > saved_selected_idx:
        self.selected = saved_selected_idx
        self.update()


def next_image(self):
    if self.selected_img_idx >= len(self.image_list) - 1:
        return
    saved_selected_idx = self.selected
    load_image(self, self.selected_img_idx + 1)

    if len(self.element_list) > saved_selected_idx:
        self.selected = saved_selected_idx
        self.update()


def next_image_with_data(self):
    if self.selected_img_idx >= len(self.image_list) - 1:
        return
    saved_element_list = self.element_list
    saved_selected_idx = self.selected
    load_image(self, self.selected_img_idx + 1)

    self.element_list = saved_element_list
    dump_annotation_file(self)

    self.selected = saved_selected_idx
    self.update()


def load_image(self, selected_img_idx):
    self.selected = -1
    self.selected_img_idx = selected_img_idx

    selected_img = self.image_list[self.selected_img_idx]
    selected_img_fullpath = os.path.join(self.demo_folder, selected_img)
    self.img_original = Image.open(selected_img_fullpath)

    # resize
    width, height = self.img_original.size
    width = width * self.multiplier
    height = height * self.multiplier
    self.img_enlarged = self.img_original.resize((width, height))
    tk_image1 = ImageTk.PhotoImage(self.img_enlarged)
    tk_image2 = ImageTk.PhotoImage(self.img_enlarged)
    self.tk_image1 = tk_image1
    self.tk_image2 = tk_image2

    # Image-1
    image_frame = self.win.children['two_image_frame']
    canvas = image_frame.children['subframe1'].children['!canvas']
    canvas.config(width=width + 3, height=height + 8)
    canvas.create_image(2, 4, image=self.tk_image1, anchor='nw')

    # Image-2
    img_label_2 = image_frame.children['subframe2'].children['img2']
    img_label_2.config(image=self.tk_image2, height=height + 8)

    # element_list
    annotation = self.annotation_list[self.selected_img_idx]
    annotation_fullpath = os.path.join(self.demo_folder, annotation)
    json_data = read_text_file(annotation_fullpath)
    self.element_list = json.loads(json_data)
    self.update()


def save_element(self, do_auto_fit=False):
    image_frame = self.win.children['two_image_frame']
    canvas = image_frame.children['subframe1'].children['!canvas']
    coords = canvas.coords(self.bbox)
    if len(coords) == 0:
        return

    x1 = round(coords[0] / self.multiplier)
    y1 = round(coords[1] / self.multiplier)
    x2 = round(coords[2] / self.multiplier)
    y2 = round(coords[3] / self.multiplier)

    element = {'coords': [x1 + self.canvas_x_offset, y1 + self.canvas_y_offset, x2 + self.canvas_x_offset,
                          y2 + self.canvas_y_offset],
               'type': DICT_TYPE['draggable_text']}
    self.element_list.append(element)

    # save as file
    dump_annotation_file(self)

    # refresh
    canvas.delete(self.bbox)
    self.selected = len(self.element_list) - 1
    if do_auto_fit:
        fit_tight_on(self, 'A')
    self.update()


def save_temp_element(self):
    self.template_element_list = self.element_list


def load_temp_element(self):
    if len(self.template_element_list) > 0:
        self.element_list = copy.deepcopy(self.template_element_list)

        dump_annotation_file(self)
        self.update()


def sort_element(self):
    selected_item = None
    if self.selected >= 0:
        selected_item = self.element_list[self.selected]
    self.element_list = sort_data(self.element_list)
    if selected_item is not None:
        target_idx = self.element_list.index(selected_item)
        self.selected = target_idx
    dump_annotation_file(self)
    self.update()


def sort_data(data):
    sorted_data = sorted(data, key=lambda x: x['coords'][1])
    for i in range(len(sorted_data) - 1):
        pin_y = sorted_data[i]['coords'][1]
        last_idx = i
        for j in range(i, len(sorted_data)):
            if sorted_data[j]['coords'][1] <= pin_y + 1:
                last_idx = j
        if last_idx != i:
            sorted_data[i:last_idx + 1] = sorted(sorted_data[i:last_idx + 1], key=lambda x: x['coords'][0])

    return sorted_data


def delete_element(self):
    if self.selected >= 0:
        del self.element_list[self.selected]
    self.selected = min(self.selected, len(self.element_list) - 1)
    dump_annotation_file(self)
    self.update()


def delete_all_element(self):
    self.element_list = []
    self.selected = -1
    dump_annotation_file(self)
    self.update()


def bbox_coordinate_controller(self, target, state):
    if isinstance(target.get(), (int, float)):
        target_value = target.get()
        if state == 'up':
            target_value += 1
        if state == 'down':
            target_value -= 1
        target.set(max(0, target_value))
        update_selected_box_coordinate(self)


def update_selected_box_coordinate(self):
    if self.selected < 0:
        return
    element = self.element_list[self.selected]
    element['coords'] = [self.x1.get(), self.y1.get(), self.x2.get(), self.y2.get()]
    dump_annotation_file(self)
    self.update()


def get_image_row_values(self, target_y, start_x, end_x):
    start_x = max(start_x, 0)
    end_x = min(end_x, self.img_original.width)
    if target_y < 0:
        target_y = 0
    if target_y >= self.img_original.height:
        target_y = self.img_original.height - 1

    row_pixels = []
    for x in range(start_x, end_x):
        r, g, b = self.img_original.getpixel((x, target_y))
        row_pixels.append((r + b + g) / 3)
    if len(row_pixels) == 0:
        r, g, b = self.img_original.getpixel((start_x, target_y))
        row_pixels.append((r + b + g) / 3)

    return row_pixels


def get_image_col_values(self, target_x, start_y, end_y):
    start_y = max(start_y, 0)
    end_y = min(end_y, self.img_original.height)
    if target_x < 0:
        target_x = 0
    if target_x >= self.img_original.width:
        target_x = self.img_original.width - 1

    col_pixels = []
    for y in range(start_y, end_y):
        r, g, b = self.img_original.getpixel((target_x, y))
        col_pixels.append((r + b + g) / 3)
    if len(col_pixels) == 0:
        r, g, b = self.img_original.getpixel((target_x, start_y))
        col_pixels.append((r + b + g) / 3)

    return col_pixels


def get_diff_score(list_a, list_b):
    if len(list_a) != len(list_b):
        print(f"ERROR ON GET _DIFF : \nlist_a:{list_a}\nlist_b:{list_b}")
        return 0
    if len(list_a) == 0:
        return 0
    diff = [abs(x - y) for x, y in zip(list_a, list_b)]

    return max(diff)


def fit_tight_on(self, target_line):
    if self.selected < 0:
        return
    target_bbox = self.element_list[self.selected]['coords']
    diff_threshold = self.fit_threshold.get()

    # left -> right
    if target_line == 'L' or target_line == 'A':
        target_fit_value = target_bbox[0]
        destination_idx = target_bbox[2]
        start_point = target_bbox[1]
        end_point = target_bbox[3]
        start_values = get_image_col_values(self, target_fit_value, start_point, end_point)
        for potential_idx in range(target_fit_value + 1, destination_idx - 1):
            next_values = get_image_col_values(self, potential_idx, start_point, end_point)
            diff_score = get_diff_score(next_values, start_values)
            if diff_score > diff_threshold:
                target_fit_value = potential_idx - 1
                break
        target_bbox[0] = target_fit_value

    # right -> left
    if target_line == 'R' or target_line == 'A':
        target_fit_value = target_bbox[2]
        destination_idx = target_bbox[0]
        start_point = target_bbox[1]
        end_point = target_bbox[3]
        start_values = get_image_col_values(self, target_fit_value, start_point, end_point)
        for potential_idx in range(target_fit_value - 1, destination_idx + 1, -1):
            next_values = get_image_col_values(self, potential_idx, start_point, end_point)
            diff_score = get_diff_score(next_values, start_values)
            if diff_score > diff_threshold:
                target_fit_value = potential_idx + 1
                break
        target_bbox[2] = target_fit_value

    # top -> bottom
    if target_line == 'T' or target_line == 'A':
        target_fit_value = target_bbox[1]
        destination_idx = target_bbox[3]
        start_point = target_bbox[0]
        end_point = target_bbox[2]
        start_values = get_image_row_values(self, target_fit_value, start_point, end_point)
        for potential_idx in range(target_fit_value + 1, destination_idx - 1):
            next_values = get_image_row_values(self, potential_idx, start_point, end_point)
            diff_score = get_diff_score(next_values, start_values)
            if diff_score > diff_threshold:
                target_fit_value = potential_idx - 1
                break
        target_bbox[1] = target_fit_value

    # bottom -> top
    if target_line == 'B' or target_line == 'A':
        target_fit_value = target_bbox[3]
        destination_idx = target_bbox[1]
        start_point = target_bbox[0]
        end_point = target_bbox[2]
        start_values = get_image_row_values(self, target_fit_value, start_point, end_point)
        for potential_idx in range(target_fit_value - 1, destination_idx + 1, -1):
            next_values = get_image_row_values(self, potential_idx, start_point, end_point)
            diff_score = get_diff_score(next_values, start_values)
            if diff_score > diff_threshold:
                target_fit_value = potential_idx + 1
                break
        target_bbox[3] = target_fit_value

    self.element_list[self.selected]['coords'] = target_bbox

    dump_annotation_file(self)
    self.update()


def fit_tight_in(self):
    if self.selected < 0:
        return
    target_bbox = self.element_list[self.selected]['coords']
    max_col_idx = self.img_original.width - 1
    max_row_idx = self.img_original.height - 1

    # right-> max
    target_bbox[2] = min(target_bbox[2] + 1, max_col_idx)

    # left -> 0
    target_bbox[0] = max(target_bbox[0] - 1, 0)

    # bottom -> max
    target_bbox[3] = min(target_bbox[3] + 1, max_row_idx)

    # top -> 0
    target_bbox[1] = max(target_bbox[1] - 1, 0)

    self.element_list[self.selected]['coords'] = target_bbox

    dump_annotation_file(self)
    self.update()


def auto_fit_element(self):
    load_element_from_dom(self)
    tmp_selected_id = self.selected

    for idx in range(len(self.element_list)):
        self.selected = idx
        fit_tight_on(self, 'A')
        fit_tight_in(self)
        fit_tight_on(self, 'A')
    self.selected = tmp_selected_id

    dump_annotation_file(self)
    self.update()


def type_select_by_radio(self):
    if self.selected < 0:
        return
    element = self.element_list[self.selected]
    element['type'] = self.type.get()
    dump_annotation_file(self)
    self.update()


def subtype_select_by_combobox(self):
    if self.selected < 0:
        return
    element = self.element_list[self.selected]
    element['subtype'] = SUBTYPE_OPTIONS[TYPE_DICT[self.type.get()]][
        self.win.children['subtype_frame'].children['subtype'].current()]
    dump_annotation_file(self)
    self.update()


def text_entered(self):
    if self.selected < 0:
        return
    element = self.element_list[self.selected]
    element['text'] = self.text.get()
    dump_annotation_file(self)
    self.update()


def checked_clicked(self):
    if self.selected < 0:
        return
    element = self.element_list[self.selected]
    element['checked'] = str(self.checked.get())
    dump_annotation_file(self)
    self.update()


def focused_clicked(self):
    if self.selected < 0:
        return
    element = self.element_list[self.selected]
    element['focused'] = str(self.focused.get())
    dump_annotation_file(self)
    self.update()

def verbose_clicked(self):
    self.update()

def highlighted_clicked(self):
    if self.selected < 0:
        return
    element = self.element_list[self.selected]
    element['highlighted'] = str(self.highlighted.get())
    dump_annotation_file(self)
    self.update()


def convert_virtual_miniwob_to_element_list(self, processed_data_list):
    for processed_data in processed_data_list:
        x1 = processed_data['x1']
        y1 = processed_data['y1']
        x2 = processed_data['x2']
        y2 = processed_data['y2']

        element_data = {}
        # coords
        element_data['coords'] = [x1, y1, x2, y2]
        # type
        if processed_data['type'] in DICT_TYPE.keys():
            element_data['type'] = DICT_TYPE[processed_data['type']]
        else:
            element_data['type'] = DICT_TYPE['draggable_text']

        keys_used = KEYS_USED[processed_data['type']]
        processed_data.pop('type')
        for pk in keys_used:
            if pk in processed_data.keys():
                element_data[pk] = processed_data[pk]
        self.element_list.append(element_data)

    dump_annotation_file(self)
    self.update()


def load_element_from_dom(self):
    main_virtual_miniWob = self.ask_main_controller("VirtualMiniWob")
    main_virtual_miniWob.df_select_option.set(2)
    main_virtual_miniWob.update()
    if main_virtual_miniWob.df is not None:
        processed_data_list = main_virtual_miniWob.df.to_dict('records')
    else:
        processed_data_list = []
    convert_virtual_miniwob_to_element_list(self, processed_data_list)


def load_element_from_visual_observer(self):
    main_visual_observer = self.ask_main_controller("VisualObserver")
    self.element_list = main_visual_observer.element_list.copy()
    dump_annotation_file(self)
    self.update()


def make_clean_element_list(self):
    clean_element_list = []
    for element in self.element_list:
        if "type" not in element.keys():
            raise Exception(f"data something wrong : {element}")

        if element["type"] == 100:  # breakdown case
            converted_dict = element

        else:
            type_val = TYPE_DICT[element["type"]]
            keys_used = KEYS_USED[type_val]
            converted_dict = {}
            for pk in keys_used:
                if pk in element.keys():
                    converted_dict[pk] = element[pk]
                else:
                    if pk == 'text':
                        converted_dict[pk] = ""
                    else:
                        converted_dict[pk] = 'False'
        clean_element_list.append(converted_dict)
    self.element_list = copy.deepcopy(clean_element_list)


def dump_annotation_file(self):
    annotation = self.annotation_list[self.selected_img_idx]
    annotation_fullpath = os.path.join(self.demo_folder, annotation)
    make_clean_element_list(self)  # Is this command needed here?
    with open(annotation_fullpath, 'w', encoding='utf-16') as f:
        json.dump(self.element_list, f, indent=4)


def update(self):
    path_text = self.win.children['path_settings_frame'].children['path_text']

    if self.demo_folder is None:
        path_text.config(text="Image Folder Not Selected!")
    else:
        foldername = os.path.basename(self.demo_folder)
        path_text.config(text=foldername)

        index_text = self.win.children['img_select_frame'].children['index_text']
        index_text.config(text=f"{self.selected_img_idx + 1:03}/{len(self.image_list):03}")

    button_prev = self.win.children['img_select_frame'].children['prev']
    button_next = self.win.children['img_select_frame'].children['next']
    button_next_with_data = self.win.children['img_select_frame'].children['next_with_data']
    if self.selected_img_idx <= 0:
        button_prev.configure(state="disabled")
    else:
        button_prev.config(state="active")
    if self.selected_img_idx >= len(self.image_list) - 1:
        button_next.configure(state="disabled")
        button_next_with_data.configure(state="disabled")
    else:
        button_next.config(state="active")
        button_next_with_data.config(state="active")

    # ROI BBOX
    #####################################################
    image2 = self.img_enlarged.copy()
    draw = ImageDraw.Draw(image2)
    for id, element in enumerate(self.element_list):
        (x1, y1, x2, y2) = element['coords']

        x1 = x1 * self.multiplier
        x2 = x2 * self.multiplier
        y1 = y1 * self.multiplier
        y2 = y2 * self.multiplier
        color = elements_util.to_color(element)
        b_color = (color[0] + 10, color[1] + 10, color[2] + 10)
        if id == self.selected:
            draw.rectangle((x1, y1, x2, y2), outline='red', width=5)
        else:
            draw.rectangle((x1, y1, x2, y2), outline=b_color, width=2)

        if 'checked' in element.keys() and element['checked'] == 'True':
            draw.rectangle((x1, y1, x2, y2), outline=(0, 255, 0), width=3)
        if 'focused' in element.keys() and element['focused'] == 'True':
            draw.rectangle((x1, y1, x2, y2), outline=(0, 255, 175), width=3)
        if 'highlighted' in element.keys() and element['highlighted'] == 'True':
            draw.rectangle((x1, y1, x2, y2), outline=(0, 255, 255), width=3)
        
        if self.verbose.get():
            # Element Description on screen
            position = (x1, y1-10)   
            text = elements_util.to_string_without_coord(element)
            text_bbox = draw.textbbox(position, text)        
            
            draw.rectangle(text_bbox, fill=color)
            position = (x1+1, y1-10)
            draw.text(position, text,  fill=(255,255,255,0), width=1)

    tk_image2 = ImageTk.PhotoImage(image2)
    self.tk_image2 = tk_image2

    image_frame = self.win.children['two_image_frame']
    img_label_2 = image_frame.children['subframe2'].children['img2']
    img_label_2.config(image=self.tk_image2)

    # List_Box
    #####################################################
    # List_Box
    listbox_frame = self.win.children['two_image_frame'].children['list_frame']
    listbox = listbox_frame.children['!listbox']
    listbox.delete(0, 'end')  # delete all

    for idx, element in enumerate(self.element_list):
        type_str = '(No Type)'
        if "type" in element and element['type'] in TYPE_DICT.keys():
            type_str = TYPE_DICT[element['type']]
        if "type" in element and element['type'] == 100:
            type_str = "(breakdown) " + element['description']
        disp_str = f" {idx + 1:02}: {type_str}"
        listbox.insert('end', disp_str)

    if self.selected >= 0:
        listbox.selection_set(self.selected)
        listbox.activate(self.selected)

    # Element Descriptions
    #####################################################
    x1 = -1
    x2 = -1
    y1 = -1
    y2 = -1
    type = 99
    subtype = ""
    text = ""
    checked = False
    focused = False
    highlighted = False
    if self.selected >= 0:
        element = self.element_list[self.selected]
        (x1, y1, x2, y2) = element['coords']
        if "type" in element:
            type = element['type']
        if "subtype" in element:
            subtype = element['subtype']
        if "text" in element:
            text = element['text']
        if "checked" in element:
            checked = element['checked']
        if "focused" in element:
            focused = element['focused']
        if "highlighted" in element:
            highlighted = element['highlighted']

    self.x1.set(x1)
    self.x2.set(x2)
    self.y1.set(y1)
    self.y2.set(y2)
    self.type.set(type)
    self.subtype.set(subtype)
    self.text.set(text)
    self.checked.set(checked)
    self.focused.set(focused)
    self.highlighted.set(highlighted)

    # Masking by Type
    #####################################################
    type_val = TYPE_DICT[self.type.get()]
    keys_used = KEYS_USED[type_val]
    if type_val in SUBTYPE_OPTIONS.keys():
        subtype_options = SUBTYPE_OPTIONS[type_val]
    else:
        subtype_options = []

    if subtype not in subtype_options:
        subtype = ''
        self.subtype.set(subtype)

    for subframe_name in ['subframe1', 'subframe2', 'subframe3', 'subframe4', 'subframe5']:
        frame = self.win.children['xxyy_frame'].children[subframe_name]
        if 'coords' in keys_used:
            for child in frame.winfo_children():
                child.configure(state='normal')
        else:
            for child in frame.winfo_children():
                child.configure(state='disabled')

    type_dicts = get_per_line_type_dicts()

    for i in range(len(type_dicts)):
        subframe_name = f'subframe{i + 1}'
        frame = self.win.children['type_frame'].children[subframe_name]
        if 'type' in keys_used:
            for child in frame.winfo_children():
                child.configure(state='normal')
        else:
            for child in frame.winfo_children():
                child.configure(state='disabled')

    ui = self.win.children['subtype_frame'].children['subtype']
    if 'subtype' in keys_used:
        ui.config(state="readonly")
        ui.config(values=subtype_options)
        ui.set(subtype)
    else:
        ui.config(state="disabled")
        ui.set('')

    ui = self.win.children['text_frame'].children['!entry']
    if 'text' in keys_used:
        ui.config(state="normal")
    else:
        ui.config(state="disabled")

    ui = self.win.children['bool_frame'].children['checked']
    if 'checked' in keys_used:
        ui.config(state="normal")
    else:
        ui.config(state="disabled")

    ui = self.win.children['bool_frame'].children['focused']
    if 'focused' in keys_used:
        ui.config(state="normal")
    else:
        ui.config(state="disabled")

    ui = self.win.children['bool_frame'].children['highlighted']
    if 'highlighted' in keys_used:
        ui.config(state="normal")
    else:
        ui.config(state="disabled")


def get_per_line_type_dicts(n_per_line: int = 6):
    # Annotator���� TYPE_DICT ���� n_per_line ������ �ٹٲ��Ͽ� ����ϱ� ���� ���Ǵ� �Լ���.
    # elements_util�� ���ǵ� TYPE_DICT �� �߿��� key ���� 100 �̸��� ������ n_per_line ������ ���� 2���� ����Ʈ�� �����.
    type_dict = {key: value for key, value in elements_util.TYPE_DICT.items() if key < 100}  # Exclude key=100
    type_dict_items = list(type_dict.copy().items())
    type_dicts = list()
    while type_dict_items:
        temp = list()
        for _ in range(min(n_per_line, len(type_dict_items))):
            item = type_dict_items.pop(0)
            temp.append(item)
        type_dicts.append(temp)
    return type_dicts
