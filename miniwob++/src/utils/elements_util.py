import copy
import json
import os

import numpy as np
from sklearn.cluster import KMeans

from src.utils.file import read_text_file

TYPE_DICT = {}
TYPE_DICT[1] = "text"
TYPE_DICT[2] = "hyperlink"
TYPE_DICT[3] = "tabled_text"
TYPE_DICT[11] = "button"
TYPE_DICT[12] = "radio"
TYPE_DICT[13] = "checkbox"
TYPE_DICT[20] = "dropdown"
TYPE_DICT[30] = "input_field"
TYPE_DICT[31] = "text_area"
TYPE_DICT[32] = "resize_handle"
TYPE_DICT[40] = "scrollbar_v"
TYPE_DICT[50] = "icon"
TYPE_DICT[51] = "shape"
TYPE_DICT[99] = "draggable_text"

TYPE_DICT[100] = "breakdown_sub_element_type_that_should_not_be_handled_by_annotator"

ALL_KEYS = ['type', 'coords', 'text', 'checked', 'focused', 'highlighted']

BASIC_KEYS = ['type', 'coords']

KEYS_USED = {
    'text': BASIC_KEYS + ['text', 'highlighted'],
    'hyperlink': BASIC_KEYS + ['text', 'highlighted'],
    'tabled_text': BASIC_KEYS + ['text', 'highlighted'],
    'button': BASIC_KEYS + ['text', 'focused'],
    'radio': BASIC_KEYS + ['checked', 'text'],
    'checkbox': BASIC_KEYS + ['checked', 'text'],
    'dropdown': BASIC_KEYS + ['text', 'focused'],
    'input_field': BASIC_KEYS + ['text', 'focused'],
    'text_area': BASIC_KEYS + ['focused'],
    'resize_handle': BASIC_KEYS,
    'scrollbar_v': BASIC_KEYS,
    'draggable_text': BASIC_KEYS + ['text'],
    'icon': BASIC_KEYS + ['subtype', 'checked'],
    'shape': BASIC_KEYS + ['subtype'],

    'breakdown_sub_element_type_that_should_not_be_handled_by_annotator': [],
}

SUBTYPE_OPTIONS = {'icon': ["back", "delete", "important", "forward", "reply", "retweet", "like", "share", "menu", "search", "send"],
                   'shape': ["point", "line", "circle", "triangle", "rectangle"]
                   }


def to_string(element, add_visible=False):
    if len(element) == 0:
        return f'{{}}'

    if element['type'] == 100:  # breakdown case
        desc = element['description']
        if add_visible:
            desc = desc[:-1] + f", visible: {element['visible']}" + "}"
        return desc

    desc = f'{{'
    pair_list = []

    # Type
    type_num = element['type']
    type = TYPE_DICT[type_num]
    pair_list.append(f"type: {type}")

    coords = element['coords']
    x1 = coords[0]
    x2 = coords[2]
    y1 = coords[1]
    y2 = coords[3]

    x = round((x1 + x2) / 2)
    y = round((y1 + y2) / 2)
    pair_list.append(f"X: {x} [{x1}-{x2}]")
    pair_list.append(f"Y: {y} [{y1}-{y2}]")

    for key in KEYS_USED[type]:
        if key == 'subtype':
            if 'subtype' in element:
                pair_list.append(f'subtype: "{element["subtype"]}"')
            else:
                pair_list.append(f'subtype: ""')

        if key == 'text':
            if 'text' in element:
                pair_list.append(f'text: "{element["text"]}"')
            else:
                pair_list.append(f'text: ""')

        if key in ['checked', 'focused', 'highlighted']:
            if key in element and element[key] == "True":
                pair_list.append(f'{key}: True')
            else:
                pair_list.append(f'{key}: False')

    if add_visible:
        pair_list.append(f"visible: {element['visible']}")
    desc += ', '.join(pair_list)
    desc += '}'

    return desc

def to_string_without_coord(element, add_visible=False):
    if len(element) == 0:
        return f'{{}}'

    if element['type'] == 100:  # breakdown case
        desc = element['description']
        if add_visible:
            desc = desc[:-1] + f", visible: {element['visible']}" + "}"
        return desc

    desc = f'{{'
    pair_list = []

    # Type
    type_num = element['type']
    type_name = TYPE_DICT[type_num]
    pair_list.append(f"type: {type_name}")

    for key in KEYS_USED[type_name]:
        if key == 'subtype':
            if 'subtype' in element:
                pair_list.append(f'subtype: "{element["subtype"]}"')
            else:
                pair_list.append(f'subtype: ""')

        if key == 'text':
            if 'text' in element:
                pair_list.append(f'text: "{element["text"]}"')
            else:
                pair_list.append(f'text: ""')

        if key in ['checked', 'focused', 'highlighted']:
            if key in element and element[key] == "True":
                pair_list.append(f'{key}: True')
            else:
                pass

    if add_visible:
        pair_list.append(f"visible: {element['visible']}")
    desc += ', '.join(pair_list)
    desc += '}'

    return desc

def get_default_rgb_by_element_type(type_idx):
    if type_idx % 3 == 0:
        r_value = (type_idx / len(TYPE_DICT) ) * 255
        r_value = 255 - r_value
    else:
        r_value = (type_idx / len(TYPE_DICT) ) * 255
    
    if type_idx % 2 == 0:
        g_value = 50+ ((len(TYPE_DICT)-type_idx) / len(TYPE_DICT) ) * 205
        b_value = 100 + (type_idx / len(TYPE_DICT) ) * 155
    else:
        g_value = (type_idx / len(TYPE_DICT) ) * 255
        b_value = ((len(TYPE_DICT)-type_idx) / len(TYPE_DICT) ) * 255

    return r_value, g_value, b_value

def to_color(element, add_visible=False):
    if len(element) == 0:
        return 0,0,0

    if element['type'] == 100:  # breakdown case
        desc = element['description']
        if add_visible:
            desc = desc[:-1] + f", visible: {element['visible']}" + "}"
        return 100,100,100

    # Type
    type_num = element['type']
    type_name = TYPE_DICT[type_num]
    type_idx = list(KEYS_USED.keys()).index(type_name) + 1

    r_value, g_value, b_value = get_default_rgb_by_element_type(type_idx)
    
    for key in KEYS_USED[type_name]:
        if key == 'subtype' and 'subtype' in element:
            if element["subtype"] in SUBTYPE_OPTIONS['icon']:
                subtype_idx = SUBTYPE_OPTIONS['icon'].index(element["subtype"])+1
                if subtype_idx % 2 == 0:
                    g_value = subtype_idx  * 30
                    b_value = subtype_idx  * 10
                else:
                    r_value = subtype_idx  * 30
                    g_value = subtype_idx  * 10
                    b_value = subtype_idx  * 15
            elif element["subtype"] in SUBTYPE_OPTIONS['shape']:
                subtype_idx = SUBTYPE_OPTIONS['shape'].index(element["subtype"])+1
                r_value = (subtype_idx/len(SUBTYPE_OPTIONS['shape'])) * 255
                g_value = (subtype_idx/len(SUBTYPE_OPTIONS['shape'])) * 30
                b_value = (subtype_idx/len(SUBTYPE_OPTIONS['shape'])) * 70
                b_value = 200 - b_value
        elif key == 'text':
            g_value += 5
        elif key == 'checked':
            b_value -= 50
        elif key == 'focused':
            g_value -= 50
            b_value -= 50
        elif key == 'highlighted':
            g_value -= 50
            

    return int(r_value), int(g_value), int(b_value)


def find_by_xy(element_list, x, y):
    found_id_list = []
    found_dist_list = []
    found_type_list = []
    found_area_list = []

    for id, element in element_list.items():
        coords = element['coords']
        x1 = coords[0]
        x2 = coords[2]
        y1 = coords[1]
        y2 = coords[3]

        if x >= x1 and x <= x2 and y >= y1 and y <= y2:
            found_id_list.append(id)
            xm = (x1 + x2) / 2
            ym = (y1 + y2) / 2
            dist_squared = (xm - x) * (xm - x) + (ym - y) * (ym - y)
            found_dist_list.append(dist_squared)
            found_type_list.append(element['type'])
            found_area_list.append((x2 - x1) * (y2 - y1))

    if len(found_id_list) == 0:
        return -1

    if len(found_id_list) == 1:
        return found_id_list[0]

    if len(found_id_list) > 1:
        if all(x == found_type_list[0] for x in found_type_list):
            # When the objects are of the same types
            # find shorted distance from the center of each objects
            min_index = found_dist_list.index(min(found_dist_list))
            id = found_id_list[min_index]

        else:
            # Use the smaller object, when two objects have different types
            min_index = found_area_list.index(min(found_area_list))
            id = found_id_list[min_index]
        return id


def get_no_overlap_xy_on_target_element(tx1, tx2, ty1, ty2, overlapping_element_list):
    xy_list = []
    for x in range(tx1 + 1, tx2):
        for y in range(ty1 + 1, ty2):
            FLAG__No_Overlap = True
            for element in overlapping_element_list:
                coords = element['coords']
                x1 = coords[0]
                x2 = coords[2]
                y1 = coords[1]
                y2 = coords[3]
                if x1 <= x and x <= x2 and y1 <= y and y <= y2:
                    FLAG__No_Overlap = False
            if FLAG__No_Overlap:
                xy_list.append((x, y))
    return xy_list

def get_xy_for_click(element_list, element_id):
    target_element = element_list[element_id]
    coords = target_element['coords']
    tx1 = coords[0]
    tx2 = coords[2]
    ty1 = coords[1]
    ty2 = coords[3]

    # Find Overlapping elements
    overlapping_element_list = []
    for id, element in element_list.items():
        # Exclude invisible
        if not element['visible']:
            continue

        # Exclude Self
        if id == element_id:
            continue

        # Exclude No-Overlap
        coords = element['coords']
        x1 = coords[0]
        x2 = coords[2]
        y1 = coords[1]
        y2 = coords[3]
        if x1 >= tx2 or x2 <= tx1 or y1 >= ty2 or y2 <= ty1:
            continue

        # Exclude Container
        if x1 <= tx1 and x2 >= tx2 and y1 <= ty1 and y2 >= ty2:
            continue

        overlapping_element_list.append(element)

    # If No Overlap, just return the center
    if len(overlapping_element_list) == 0:
        xm = round((tx1 + tx2) / 2)
        ym = round((ty1 + ty2) / 2)

        return xm, ym

    # Make 3 Clusters and return the center of the largest cluster
    xy_list = get_no_overlap_xy_on_target_element(tx1, tx2, ty1, ty2, overlapping_element_list)

    if len(xy_list) < 3:
        xm = round((tx1 + tx2) / 2)
        ym = round((ty1 + ty2) / 2)

        return xm, ym

    X = np.array(xy_list)  # convert the list to a numpy array
    kmeans = KMeans(n_clusters=3, n_init='auto')  # create a KMeans object with 3 clusters
    kmeans.fit(X)  # fit the KMeans object to the data
    labels = kmeans.labels_  # get the cluster labels for each point
    largest_cluster_mean = np.mean(X[labels == np.argmax(np.bincount(labels))], axis=0)
    (xm, ym) = largest_cluster_mean
    xm = round(xm)
    ym = round(ym)
    return xm, ym


def find_matching_element(element_list, old_element):
    coords = old_element['coords']
    old_x1 = coords[0]
    old_x2 = coords[2]
    old_y1 = coords[1]
    old_y2 = coords[3]

    found_id_list = []
    found_dist_list = []
    for id, element in element_list.items():

        if element['type'] == old_element['type']:
            found_id_list.append(id)

            coords = element['coords']
            x1 = coords[0]
            x2 = coords[2]
            y1 = coords[1]
            y2 = coords[3]
            dist = abs(old_x1 - x1) + abs(old_x2 - x2) + abs(old_y1 - y1) + abs(old_y2 - y2)
            found_dist_list.append(dist)

    if len(found_id_list) == 0:
        return -1

    if len(found_id_list) == 1:
        return found_id_list[0]

    if len(found_id_list) > 1:
        min_index = found_dist_list.index(min(found_dist_list))
        idx = found_id_list[min_index]
        return idx


def get_element_list_from_annotation_file(job_folder, action_list, action_idx):
    action = action_list[action_idx]
    annotation = action['final_image'][:-3] + "json"
    annotation_fullpath = os.path.join(job_folder, annotation)
    json_data = read_text_file(annotation_fullpath)
    element_list = json.loads(json_data)

    return element_list


def load_screen_history(job_folder):
    # Open the JSON file and read its contents
    json_file_path = os.path.join(job_folder, "screen_history.json")
    json_data = read_text_file(json_file_path)
    # Convert the JSON data into a dictionary object
    screen_history = json.loads(json_data)
    return [{int(k): e for k, e in el.items()} for el in screen_history]


def dump_screen_history(job_folder, action_list, action_idx):
    screen_history = get_screen_history(job_folder, action_list, action_idx)
    json_filename = os.path.join(job_folder, "screen_history.json")
    with open(json_filename, "w", encoding='utf-16') as f:
        json.dump(screen_history, f, indent=4)


def get_screen_history(job_folder, action_list, action_idx):
    if action_idx < 0:
        return []

    curr = get_element_list_from_annotation_file(job_folder, action_list, action_idx)
    for i, e in enumerate(curr):
        # init
        e["id"] = i + 1
        e["visible"] = True
    curr = {e["id"]: e for e in curr}  # to dict

    if action_idx == 0:
        return [curr]

    screen_history = load_screen_history(job_folder)
    screen_history = screen_history[:action_idx]  # trim, if future info exist
    prev = screen_history[action_idx - 1]

    comp_curr = set(ComparableElement(e) for k, e in curr.items())
    comp_prev = set(ComparableElement(e) for k, e in prev.items())
    new_id = len(comp_prev) + 1

    old = {}
    new = {}
    for e in comp_curr:
        found = False

        for f in comp_prev:
            if e == f:
                e.element["id"] = f.element["id"]
                old[e.element["id"]] = e.element
                comp_prev.remove(f)
                found = True
                break

        if not found:
            for f in comp_prev:
                if e.equal_by_type(f) and e.equal_by_text(f):
                    e.element["id"] = f.element["id"]
                    old[e.element["id"]] = e.element
                    comp_prev.remove(f)
                    found = True
                    break

        if not found:
            e.element["id"] = new_id
            new[e.element["id"]] = e.element
            new_id += 1

    sorted_elements = copy.deepcopy(prev)
    sorted_elements.update(new)
    for _, e in old.items():
        sorted_elements[e["id"]] = e

    for e in comp_prev:
        sorted_elements[e.element["id"]]["visible"] = False

    screen_history.append(sorted_elements)
    return screen_history


def get_sorted_elements(job_folder, action_list, action_idx, visible_only=True):
    screen_history = get_screen_history(job_folder, action_list, action_idx)
    sorted_elements = screen_history[action_idx]
    if visible_only:
        sorted_elements = {k: e for k, e in sorted_elements.items() if e["visible"]}
    return sorted_elements


class ComparableElement:
    def __init__(self, element):
        self.element = element

    def __hash__(self):
        return hash(self.element['type'])

    def __eq__(self, other):
        return (self.equal_by_type(other) and
                self.equal_by_text(other) and
                self.equal_by_position(other))

    def equal_by_type(self, other):
        return self.element['type'] == other.element['type']

    def equal_by_text(self, other):
        return equal_by_text(self.element, other.element)

    def equal_by_position(self, other):
        return (equal_by_IoU(self.element, other.element, 0.8) or
                equal_by_pixel(self.element, other.element, 2))


def equal_by_text(elt, elt_o):
    if elt['type'] in [1, 2, 3, 11, 99]:
        return elt.get('text') == elt_o.get('text')
    else:
        return True


def equal_by_IoU(elt, elt_o, threshold=0.7):
    x1, y1, x2, y2 = elt['coords']
    x1_o, y1_o, x2_o, y2_o = elt_o['coords']

    if x1 >= x2_o or x2 <= x1_o or y1 >= y2_o or y2 <= y1_o:
        return False

    x1_i = max(x1, x1_o)
    y1_i = max(y1, y1_o)
    x2_i = min(x2, x2_o)
    y2_i = min(y2, y2_o)

    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    area_o = (x2_o - x1_o + 1) * (y2_o - y1_o + 1)
    area_i = (x2_i - x1_i + 1) * (y2_i - y1_i + 1)

    iou = area_i / (area + area_o - area_i)
    return iou >= threshold


def equal_by_pixel(elt, elt_o, threshold=2):
    x1, y1, x2, y2 = elt['coords']
    x1_o, y1_o, x2_o, y2_o = elt_o['coords']

    x1_d = abs(x1 - x1_o)
    y1_d = abs(y1 - y1_o)
    x2_d = abs(x2 - x2_o)
    y2_d = abs(y2 - y2_o)

    return x1_d <= threshold and y1_d <= threshold and x2_d <= threshold and y2_d <= threshold
