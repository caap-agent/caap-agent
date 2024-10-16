
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans

def Breakdown__ScrollbarV(element, png_fullpath):

    sub_element_list = []

    coords = element['coords']
    x1 = coords[0]
    x2 = coords[2]
    y1 = coords[1]
    y2 = coords[3]

    w = x2-x1
    h = y2-y1

    FLAG__buttons_only = False
    if h <= 2*w:
        FLAG__buttons_only = True

    up_button_coords = coords.copy()
    up_button_coords[3] = y1 + w
    down_button_coords = coords.copy()
    down_button_coords[1] = y2 - w

    if FLAG__buttons_only:
        # Modify the top/bottom button size to equal halves
        middle_y = round((y1+y2)/2)
        up_button_coords[3] = middle_y
        down_button_coords = coords.copy()
        down_button_coords[1] = middle_y

    coords = up_button_coords
    description = "{type: scrollbar_up_button}"
    description = _add_coords_to_description(coords, description)
    element = {'type': 100, 'coords': coords, 'description': description}
    sub_element_list.append(element)

    coords = down_button_coords
    description = "{type: scrollbar_down_button}"
    description = _add_coords_to_description(coords, description)
    element = {'type': 100, 'coords': coords, 'description': description}
    sub_element_list.append(element)

    if not FLAG__buttons_only:
        thumb_coords = coords.copy()

        y_min = y1 + w
        y_max = y2 - w

        img = Image.open(png_fullpath)
        img = img.crop((x1, y_min, x2, y_max))
        img = img.convert('L')  # B&W

        img_array = np.array(img)
        row_sums = np.sum(img_array, axis=1)

        # Make two clusters, and find the middle value
        kmeans = KMeans(n_clusters=2, n_init='auto').fit(row_sums.reshape(-1, 1))
        threshold = np.mean(kmeans.cluster_centers_)

        # I am relaying on that the thumb is colored darker (low value). Maybe improve the code Later
        binary_array = row_sums < threshold
        thumb_size = binary_array.sum().item()

        # Use moving window to find the max overlap
        max_sum = -np.inf
        ind_start = 0
        ind_stop = 0
        for i in range(len(binary_array) - thumb_size + 1):
            window = np.zeros_like(binary_array)
            window[i:i+thumb_size] = 1
            window_sum = np.sum(binary_array * window)
            if window_sum > max_sum:
                max_sum = window_sum
                ind_start = i
                ind_stop = i + thumb_size - 1

        thumb_coords[1] = y1 + w + ind_start
        thumb_coords[3] = y1 + w + ind_stop

        if thumb_coords[1] < thumb_coords[3] and (thumb_coords[3] - thumb_coords[1]) > 3:
            coords = thumb_coords
            description = "{type: scrollbar_thumb}"
            description = _add_coords_to_description(coords, description)
            element = {'type': 100, 'coords': coords, 'description': description}
            sub_element_list.append(element)

    return sub_element_list


def _add_coords_to_description(coords, description):
    pair_list = []

    x1 = coords[0]
    x2 = coords[2]
    y1 = coords[1]
    y2 = coords[3]

    x = round((x1+x2)/2)
    y = round((y1+y2)/2)
    pair_list.append(f"X: {x} [{x1}-{x2}]")
    pair_list.append(f"Y: {y} [{y1}-{y2}]")

    desc = description[:-1] + ', '
    desc += ', '.join(pair_list)
    desc += '}'

    return desc