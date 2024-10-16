import tkinter as tk
from tkinter import ttk
import os
from src._base_window import BaseWindow
from src.supports import annotator_support
from src.utils.tk_window_util import tk_window_config

text_bind_keyword_focusin = "<FocusIn>"
text_bind_keyword_escape = "<Escape>"
text_bind_keyword_focusout = "<FocusOut>"

class Annotator(BaseWindow):

    def __init__(self, func):
        BaseWindow.__init__(self,
                            func=func,
                            title="Annotator",
                            width=850,
                            height=850,
                            support=annotator_support)

        self.win.bind("<Left>", self.press_prev_image)
        self.win.bind("<Right>", self.press_next_image)
        self.win.bind("<space>", self.save_bbox_on_canvas)
        self.win.bind("<t>", self.save_tight_bbox_on_canvas)

        # Folders

        # Data
        self.action_list = None
        self.image_list = []
        self.selected_img_idx = 0
        self.annotation_list = []
        self.demo_folder_list = []
        self.demo_idx = -1

        self.multiplier = 2  # Image Size Multiplier
        self.img_original = None
        self.img_enlarged = None
        self.tk_image1 = None
        self.tk_image2 = None
        self.FLAG__clicked = False
        self.clicked_x = None
        self.clicked_y = None
        self.hl = None
        self.vl = None
        self.bbox = None
        self.canvas_x_offset = -1
        self.canvas_y_offset = -2
        self.fit_threshold = tk.IntVar()
        self.fit_threshold.set(50)

        self.element_list = []
        self.selected = -1
        self.x1 = tk.IntVar()
        self.x2 = tk.IntVar()
        self.y1 = tk.IntVar()
        self.y2 = tk.IntVar()
        self.type = tk.IntVar()  # 1-..., 2-...,
        self.subtype = tk.StringVar()
        self.text = tk.StringVar()
        self.checked = tk.BooleanVar()
        self.focused = tk.BooleanVar()
        self.highlighted = tk.BooleanVar()

        self.template_element_list = []

        # Show data description
        self.verbose = tk.BooleanVar()

        # Layout
        tk_window_config(self.win, self.data_path, os.path.basename(__file__))
        self.draw_layout()

        # Load Blank
        annotator_support.load(self, demo_folder=self.blank_folder)

    def draw_layout(self):
        frame = tk.Frame(self.win)
        frame.pack(padx=5, pady=5, fill='x', side='bottom')
        button = tk.Button(frame, width=20, text="update", command=self.update)
        button.pack()

        frame = tk.Frame(self.win, name='path_settings_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__Path_Settings(frame)

        frame = tk.Frame(self.win, name='img_select_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__Image_Select(frame)

        frame = tk.Frame(self.win, name='operations_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__Operations(frame)

        frame = tk.Frame(self.win, name='two_image_frame')
        frame.pack(padx=5, pady=5)
        self.fill_frame__two_images_N_element_list(frame)

        separator = ttk.Separator(self.win, orient='horizontal')
        separator.pack(fill='x', padx=5, pady=5)

        frame = tk.Frame(self.win, name='xxyy_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__xxyy(frame)

        frame = tk.Frame(self.win, name='type_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__type(frame)

        frame = tk.Frame(self.win, name='subtype_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__subtype(frame)

        frame = tk.Frame(self.win, name='text_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__text(frame)

        frame = tk.Frame(self.win, name='bool_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__BOOLS(frame)

        frame = tk.Frame(self.win, name='get_info_from_outside')
        frame.pack(padx=5, pady=5, fill='x')

        self.fill_frame__info_from_outside(frame)

    def fill_frame__Path_Settings(self, frame):

        button = tk.Button(frame, width=8, height=1, text="DIR",
                           command=lambda: os.startfile(os.path.abspath(self.demo_folder_base)))
        button.pack(side='left')

        button = tk.Button(frame, width=8, height=1, text="Load",
                           command=self.load)
        button.pack(side='left')

        button = tk.Button(frame, width=8, height=1, text="Prev",
                           command=self.get_prev_dir)
        button.pack(side='left')

        button = tk.Button(frame, width=8, height=1, text="Next",
                           command=self.get_next_dir)
        button.pack(side='left')

        txt_label = tk.Label(frame, text="  ")
        txt_label.pack(side='left')

        txt_label = tk.Label(frame, text="...", name='path_text')
        txt_label.pack(side='left')

    def load(self, demo_folder=None, selected_img_idx=0):
        annotator_support.load(self, demo_folder, selected_img_idx)

    def get_prev_dir(self):
        annotator_support.get_prev_dir(self)

    def get_next_dir(self):
        annotator_support.get_next_dir(self)

    def press_prev_image(self, event):
        annotator_support.prev_image(self)

    def press_next_image(self, event):
        annotator_support.next_image(self)

    def fill_frame__Image_Select(self, frame):

        txt_label = tk.Label(frame, text="IMG:")
        txt_label.pack(side='left')

        txt_label = tk.Label(frame, text="xxx/xxx", name='index_text')
        txt_label.pack(side='left')

        txt_label = tk.Label(frame, text=" ")
        txt_label.pack(side='left')

        button = tk.Button(frame, width=10, text='<< Prev', name='prev',
                           command=self.prev_image)
        button.pack(side='left')
        button = tk.Button(frame, width=10, text='Next >>', name='next',
                           command=self.next_image)
        button.pack(side='left')
        button = tk.Button(frame, width=20, text='Next with data >>', name='next_with_data',
                           command=self.next_image_with_data)
        button.pack(side='left')

    def prev_image(self):
        annotator_support.prev_image(self)

    def next_image(self):
        annotator_support.next_image(self)

    def next_image_with_data(self):
        annotator_support.next_image_with_data(self)

    def fill_frame__Operations(self, frame):
        subframe = tk.Frame(frame, name='subframe1')
        subframe.pack(side='left', fill='x')

        button = tk.Button(subframe, width=25, text='Save Element', name='save_element_button',
                           command=self.save_element)
        button.pack(side='left')

        subframe = tk.Frame(frame, name='subframe2')
        subframe.pack(side='right', fill='x')

        button = tk.Button(subframe, width=5, text='ALL',
                           command=self.delete_all_element)
        button.pack(side='right', fill='x')

        button = tk.Button(subframe, width=12, text='Delete',
                           command=self.delete_element)
        button.pack(side='right', fill='x')

        button = tk.Button(subframe, width=12, text='Sort',
                           command=self.sort_element)
        button.pack(side='right', fill='x')

        checkbox = tk.Checkbutton(subframe, text="", variable=self.verbose, command=self.verbose_clicked,
                                  name='verbose')
        checkbox.pack(side='right', fil='x')
        txt_label = tk.Label(subframe, text="  verbose:")
        txt_label.pack(side='right', fil='x')

        button = tk.Button(subframe, width=6, text='Load T',
                           command=self.load_temp_element)
        button.pack(side='right', fill='x')

        button = tk.Button(subframe, width=6, text='Save T',
                           command=self.save_temp_element)
        button.pack(side='right', fill='x')

    def save_element(self):
        annotator_support.save_element(self)

    def save_temp_element(self):
        annotator_support.save_temp_element(self)

    def load_temp_element(self):
        annotator_support.load_temp_element(self)

    def sort_element(self):
        annotator_support.sort_element(self)

    def delete_element(self):
        annotator_support.delete_element(self)

    def delete_all_element(self):
        annotator_support.delete_all_element(self)
        
    def verbose_clicked(self):
        annotator_support.verbose_clicked(self)

    def auto_fit_element(self):
        annotator_support.auto_fit_element(self)

    def save_bbox_on_canvas(self, event):
        if self.bbox is not None:
            annotator_support.save_element(self)

    def save_tight_bbox_on_canvas(self, event):
        if self.bbox is not None:
            annotator_support.save_element(self, True)

    def fill_frame__two_images_N_element_list(self, frame):
        subframe = tk.Frame(frame, name='subframe1')
        # subframe.pack(side='left')
        subframe.pack(fill='both', side='left')

        canvas = tk.Canvas(subframe, cursor='tcross')
        canvas.create_image(0, 0, image=[])
        canvas.pack()

        canvas.bind("<Button-1>", self.mouseClick)
        canvas.bind("<Motion>", self.mouseMove)

        subframe = tk.Frame(frame, name='subframe2')
        # subframe.pack(side='left')
        subframe.pack(fill='both', side='left')
        img_label = tk.Label(subframe, image=[], name='img2')
        img_label.pack()

        txt_label = tk.Label(frame, text=" ")
        txt_label.pack(fill='x', side='left')

        subframe = tk.Frame(frame, name='list_frame')
        subframe.pack(expand=True, fill='both', side='right')

        listbox = tk.Listbox(subframe, width=100, height=20, exportselection=False)
        v_scrollbar = tk.Scrollbar(subframe, orient=tk.VERTICAL, command=listbox.yview)
        v_scrollbar.pack(side='right', fill='y')
        listbox.pack(side='right', fill='both', expand=True)
        listbox.config(yscrollcommand=v_scrollbar.set)
        v_scrollbar.config(command=listbox.yview)

        listbox.bind('<<ListboxSelect>>', self.onselect)
        listbox.bind('<d>', self.delete_listbox_selected_item)

    def mouseClick(self, event):
        if not self.FLAG__clicked:
            self.clicked_x, self.clicked_y = event.x, event.y
        else:
            x1, x2 = min(self.clicked_x, event.x), max(self.clicked_x, event.x)
            y1, y2 = min(self.clicked_y, event.y), max(self.clicked_y, event.y)
            self.temp_bbox = (x1, y1, x2, y2)

        self.FLAG__clicked = not self.FLAG__clicked

    def mouseMove(self, event):
        # self.disp.config(text = 'x: %.3d, y: %.3d' %(event.x, event.y))
        image_frame = self.win.children['two_image_frame']
        canvas = image_frame.children['subframe1'].children['!canvas']
        canvas.focus_set()
        # canvas.create_line(194, 0, 194, self.tk_image1.height(), width = 1, fill='red')
        # canvas.create_line(0, 162, self.tk_image1.width(), 162, width = 1, fill='red')

        if self.hl:
            canvas.delete(self.hl)
        self.hl = canvas.create_line(0, event.y, self.tk_image1.width(), event.y, width=1)
        if self.vl:
            canvas.delete(self.vl)
        self.vl = canvas.create_line(event.x, 0, event.x, self.tk_image1.height(), width=1)
        if self.FLAG__clicked:
            if self.bbox:
                canvas.delete(self.bbox)
            self.bbox = canvas.create_rectangle(self.clicked_x, self.clicked_y, event.x, event.y,
                                                width=2, outline='red')

    def onselect(self, event):
        listbox = event.widget
        selection = listbox.curselection()
        if not selection:
            self.selected = -1
        else:
            self.selected = selection[0]

        self.update()

    def delete_listbox_selected_item(self, event):
        annotator_support.delete_element(self)

    def fill_frame__xxyy(self, frame):
        subframe = tk.Frame(frame, name='subframe1')
        subframe.pack(side='left', fill='x')
        txt_label = tk.Label(subframe, text="x1:")
        txt_label.pack(side='left')
        textbox = tk.Entry(subframe, width=5, textvariable=self.x1)
        self.textbox_event_binder(textbox)
        textbox.pack(side='left')
        button = tk.Button(subframe, height=1, text="<",
                           command=lambda: self.bbox_coordinate_controller(self.x1, 'down'))
        button.pack(side='left')
        button = tk.Button(subframe, height=1, text=">", command=lambda: self.bbox_coordinate_controller(self.x1, 'up'))
        button.pack(side='left')
        spacer = tk.Label(frame, text="", width=1)
        spacer.pack(side="left", fill="x", expand=True)

        subframe = tk.Frame(frame, name='subframe2')
        subframe.pack(side='left', fill='x')
        txt_label = tk.Label(subframe, text="x2:")
        txt_label.pack(side='left')
        textbox = tk.Entry(subframe, width=5, textvariable=self.x2)
        self.textbox_event_binder(textbox)
        textbox.pack(side='left')
        button = tk.Button(subframe, height=1, text="<",
                           command=lambda: self.bbox_coordinate_controller(self.x2, 'down'))
        button.pack(side='left')
        button = tk.Button(subframe, height=1, text=">", command=lambda: self.bbox_coordinate_controller(self.x2, 'up'))
        button.pack(side='left')
        spacer = tk.Label(frame, text="", width=1)
        spacer.pack(side="left", fill="x", expand=True)

        subframe = tk.Frame(frame, name='subframe3')
        subframe.pack(side='left', fill='x')
        txt_label = tk.Label(subframe, text="y1:")
        txt_label.pack(side='left')
        textbox = tk.Entry(subframe, width=5, textvariable=self.y1)
        self.textbox_event_binder(textbox)
        textbox.pack(side='left')
        button = tk.Button(subframe, height=1, text="▲",
                           command=lambda: self.bbox_coordinate_controller(self.y1, 'down'))
        button.pack(side='left')
        button = tk.Button(subframe, height=1, text="▼", command=lambda: self.bbox_coordinate_controller(self.y1, 'up'))
        button.pack(side='left')
        spacer = tk.Label(frame, text="", width=1)
        spacer.pack(side="left", fill="x", expand=True)

        subframe = tk.Frame(frame, name='subframe4')
        subframe.pack(side='left', fill='x')
        txt_label = tk.Label(subframe, text="y2:")
        txt_label.pack(side='left')
        textbox = tk.Entry(subframe, width=5, textvariable=self.y2)
        self.textbox_event_binder(textbox)
        textbox.pack(side='left')
        button = tk.Button(subframe, height=1, text="▲",
                           command=lambda: self.bbox_coordinate_controller(self.y2, 'down'))
        button.pack(side='left')
        button = tk.Button(subframe, height=1, text="▼", command=lambda: self.bbox_coordinate_controller(self.y2, 'up'))
        button.pack(side='left')
        spacer = tk.Label(frame, text="", width=1)
        spacer.pack(side="left", fill="x", expand=True)

        spacer = tk.Label(frame, text="", width=1)
        spacer.pack(side="left", fill="x", expand=True)
        spacer = tk.Label(frame, text="", width=1)
        spacer.pack(side="left", fill="x", expand=True)

        subframe = tk.Frame(frame, name='subframe5')
        subframe.pack(side='left', fill='x')
        button = tk.Button(subframe, width=7, text='Expand', name='fit_in_button',
                           command=self.fit_tight_in)
        button.pack(side='left')
        spacer = tk.Label(subframe, text="", width=1)
        spacer.pack(side="left", fill="x", expand=True)
        txt_label = tk.Label(subframe, text="fit threshold:")
        txt_label.pack(side='left')
        textbox = tk.Entry(subframe, width=3, textvariable=self.fit_threshold)
        self.fit_threshold_textbox_event_binder(textbox)
        textbox.pack(side='left')
        button = tk.Button(subframe, width=3, text='→', name='fit_tight_on_left',
                           command=self.fit_tight_on_left)
        button.pack(side='left')
        button = tk.Button(subframe, width=3, text='←', name='fit_tight_on_right',
                           command=self.fit_tight_on_right)
        button.pack(side='left')
        button = tk.Button(subframe, width=3, text='↓', name='fit_tight_on_top',
                           command=self.fit_tight_on_top)
        button.pack(side='left')
        button = tk.Button(subframe, width=3, text='↑', name='fit_tight_on_bottom',
                           command=self.fit_tight_on_bottom)
        button.pack(side='left')
        button = tk.Button(subframe, width=3, text='A', name='fit_tight_on_all',
                           command=self.fit_tight_on_all)
        button.pack(side='left')

    def bbox_coordinate_controller(self, target, state):
        annotator_support.bbox_coordinate_controller(self, target, state)

    def bbox_coodinate_textbox_on_enter_pressed(self, event):
        textbox = event.widget
        textbox.configure(background='white')
        self.win.focus()
        annotator_support.update_selected_box_coordinate(self)

    def textbox_event_binder(self, textbox):
        textbox.bind(text_bind_keyword_focusin, self.text_on_entry_focus)
        textbox.bind("<Return>", self.bbox_coodinate_textbox_on_enter_pressed)
        textbox.bind(text_bind_keyword_escape, self.text_on_escape)
        textbox.bind(text_bind_keyword_focusout, self.text_on_escape)

    def fit_threshold_textbox_event_binder(self, textbox):
        textbox.bind(text_bind_keyword_focusin, self.text_on_entry_focus)
        textbox.bind(text_bind_keyword_escape, self.text_on_escape)
        textbox.bind(text_bind_keyword_focusout, self.text_on_escape)

    def fit_tight_on_left(self):
        annotator_support.fit_tight_on(self, 'L')

    def fit_tight_on_right(self):
        annotator_support.fit_tight_on(self, 'R')

    def fit_tight_on_top(self):
        annotator_support.fit_tight_on(self, 'T')

    def fit_tight_on_bottom(self):
        annotator_support.fit_tight_on(self, 'B')

    def fit_tight_on_all(self):
        annotator_support.fit_tight_on(self, 'A')

    def fit_tight_in(self):
        annotator_support.fit_tight_in(self)

    def fill_frame__type(self, frame):
        width_val = 12
        type_dicts = self.support.get_per_line_type_dicts()

        for i, type_dicts_per_line in enumerate(type_dicts):
            subframe = tk.Frame(frame, name=f'subframe{i + 1}')
            subframe.pack(fill='x')
            txt_label = tk.Label(subframe, text="type:")
            txt_label.pack(side='left')
            if i > 0:
                bg_color = txt_label.cget("bg")  # invisible
                txt_label.config(fg=bg_color)
            for type_val, type_str in type_dicts_per_line:
                radio = tk.Radiobutton(subframe, width=width_val, text=type_str, variable=self.type, value=type_val,
                                       command=self.type_select_by_radio)
                radio.pack(side="left", anchor="w")

    def type_select_by_radio(self):
        annotator_support.type_select_by_radio(self)

    def fill_frame__subtype(self, frame):
        txt_label = tk.Label(frame, text="subtype:")
        txt_label.pack(side='left')
        subtype_combobox = ttk.Combobox(frame, values=[], state='readonly', name='subtype')
        subtype_combobox.bind('<<ComboboxSelected>>', self.subtype_select_by_combobox)
        subtype_combobox.pack(side='left')

    def subtype_select_by_combobox(self, event):
        annotator_support.subtype_select_by_combobox(self)

    def fill_frame__text(self, frame):
        txt_label = tk.Label(frame, text="text:")
        txt_label.pack(side='left')
        textbox = tk.Entry(frame, width=100, textvariable=self.text)
        textbox.bind(text_bind_keyword_focusin, self.text_on_entry_focus)
        textbox.bind("<Return>", self.text_on_enter_pressed)
        textbox.bind(text_bind_keyword_escape, self.text_on_escape)
        textbox.bind(text_bind_keyword_focusout, self.text_on_escape)

        textbox.pack(side='left')

    def text_on_entry_focus(self, event):
        # mark focus
        textbox = event.widget
        textbox.configure(background="#AADDFF")

    def text_on_enter_pressed(self, event):
        textbox = event.widget
        textbox.configure(background='white')
        annotator_support.text_entered(self)
        self.win.focus()

    def text_on_escape(self, event):
        textbox = event.widget
        textbox.configure(background='white')
        self.update()
        self.win.focus()

    def fill_frame__BOOLS(self, frame):
        txt_label = tk.Label(frame, text="checked:")
        txt_label.pack(side='left')
        checkbox = tk.Checkbutton(frame, text="", variable=self.checked, command=self.checked_clicked, name='checked')
        checkbox.pack(side='left')

        txt_label = tk.Label(frame, text="  focused:")
        txt_label.pack(side='left')
        checkbox = tk.Checkbutton(frame, text="", variable=self.focused, command=self.focused_clicked, name='focused')
        checkbox.pack(side='left')

        txt_label = tk.Label(frame, text="  highlighted:")
        txt_label.pack(side='left')
        checkbox = tk.Checkbutton(frame, text="", variable=self.highlighted, command=self.highlighted_clicked,
                                  name='highlighted')
        checkbox.pack(side='left')

    def checked_clicked(self):
        annotator_support.checked_clicked(self)

    def focused_clicked(self):
        annotator_support.focused_clicked(self)

    def highlighted_clicked(self):
        annotator_support.highlighted_clicked(self)

    def fill_frame__info_from_outside(self, frame):
        subframe = tk.Frame(frame, name='subframe1')
        subframe.pack(side='left', fill='x')

        button = tk.Button(subframe, width=35, text='Load Element from Virtual MiniWob',
                           name='load_element_from_dom_button',
                           command=self.load_element_from_dom)
        button.pack(side='left')

        button = tk.Button(subframe, width=12, text='Auto Fit',
                           command=self.auto_fit_element)
        button.pack(side='left', fill='x')

        spacer = tk.Label(subframe, text="", width=10)
        spacer.pack(side="left", fill="x", expand=True)

        button = tk.Button(subframe, width=30, text='Load Element from Visual Observer',
                           name='load_element_from_scree2text_button',
                           command=self.load_element_from_visual_observer)
        button.pack(side='left')

    def load_element_from_dom(self):
        annotator_support.load_element_from_dom(self)

    def load_element_from_visual_observer(self):
        annotator_support.load_element_from_visual_observer(self)
