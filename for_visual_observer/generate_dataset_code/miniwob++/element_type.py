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