import tkinter as tk
from tkinter import ttk
import os
import sys
import threading
import gymnasium

from src._base_window import BaseWindow
from src.supports import virtual_miniwob_support
from src.utils.tk_window_util import tk_window_config
from src.utils.customexception import CustomException

message_get_coord = "get coord"

class VirtualMiniWob(BaseWindow):

    def __init__(self, func):
        BaseWindow.__init__(self,
                            func=func,
                            title="Virtual MiniWob++",
                            width=700,
                            height=900,
                            support=virtual_miniwob_support)

        # Conversion
        self.conversion_folder = os.path.join("./", "DOM_conversion_rules")
        sys.path.append(self.conversion_folder)  # This is needed to import_module

        # Data
        self.env_name = None
        self.seed_num = None
        self.env = None
        self.observation = None
        self.info = None
        self.demo_action_list = None
        self.demo_idx = None

        self.multiplier = 2  # Image Size Multiplier
        self.img_original = None
        self.img_enlarged = None
        self.tk_image2 = None

        self.action_option = tk.IntVar()
        self.action_option.set(1)
        self.click_x = tk.IntVar()
        self.click_y = tk.IntVar()
        self.control_pressed = tk.BooleanVar()
        self.type_string = tk.StringVar()
        self.point_x = tk.IntVar()
        self.point_y = tk.IntVar()
        self.drag1_x = tk.IntVar()
        self.drag1_y = tk.IntVar()
        self.drag2_x = tk.IntVar()
        self.drag2_y = tk.IntVar()

        self.df_select_option = tk.IntVar()
        self.df_select_option.set(2)
        self.df_original = None
        self.df = None

        # Layout
        tk_window_config(self.win, self.data_path, os.path.basename(__file__))
        self.draw_layout()

        # Update
        self.update()

    def draw_layout(self):
        frame = tk.Frame(self.win)
        frame.pack(padx=5, pady=5, fill='x', side='bottom')
        button = tk.Button(frame, width=20, text="update", command=self.update)
        button.pack()

        frame = tk.Frame(self.win, name='open')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__Open(frame)

        frame = tk.Frame(self.win, name='two_image_frame')
        frame.pack(padx=5, pady=5)
        self.fill_frame__Image_N_Actions(frame)

        separator = ttk.Separator(self.win, orient='horizontal')
        separator.pack(fill='x', padx=5, pady=5)

        frame = tk.Frame(self.win, name='radio_frame')
        frame.pack(padx=5, pady=5, fill='x')
        self.fill_frame__conversion_radios(frame)

        frame = tk.Frame(self.win, name='dataframe_frame')
        frame.pack(padx=5, pady=5, fill='both')
        self.fill_frame__pandas(frame)

    def reset(self, env_name, seed_num):

        if self.env_name != env_name:

            self.env_name = env_name
            self.seed_num = seed_num

            try:
                self.env.close()
            except Exception:
                pass

            self.env = gymnasium.make(f"miniwob/{self.env_name}-v1",
                                      render_mode=None, wait_ms=500)
            self.observation, self.info = self.env.reset(seed=self.seed_num)

        else:
            self.seed_num = seed_num
            self.observation, self.info = self.env.reset(seed=self.seed_num)

        self.update()

    def step(self, actiontype, coords=None, text=None):
        miniwob_action = self.env.unwrapped.create_action(actiontype,
                                                          coords=coords,
                                                          text=text)

        self.observation, _, _, _, self.info = self.env.step(miniwob_action)



    def fill_frame__Open(self, frame):
        button = tk.Button(frame, width=25, text="Start Annotator Task",
                           command=self.start_annotator_task)
        button.pack(side='left')
        button = tk.Button(frame, width=12, text="Act Recorded", name='act_recorded',
                           command=self.act_recorded)
        button.pack(side='left')
        txt_label = tk.Label(frame, text=" ", name='counter')
        txt_label.pack(side='left')
        txt_label = tk.Label(frame, text=" ", name='action_desc')
        txt_label.pack(side='left')

        button = tk.Button(frame, width=25, text="Start Main Controller Task",
                               command=self.start_main_controller_task)
        button.pack(side='right')

    def start_main_controller_task(self):
        virtual_miniwob_support.start_main_controller_task(self)

    def start_annotator_task(self):
        virtual_miniwob_support.start_annotator_task(self)

    def act_recorded(self):
        virtual_miniwob_support.act_recorded(self)


    def fill_frame__Image_N_Actions(self, frame):
        subframe = tk.Frame(frame, name='subframe2')
        subframe.pack(expand = True, fill ='both', side='left')
        img_label = tk.Label(subframe, image=[], name='img2')
        img_label.pack(side='left')

        txt_label = tk.Label(frame, text="    ")
        txt_label.pack(side='left')

        subframe = tk.Frame(frame, name='action_panel')
        subframe.pack(side='left', fill ='both')
        self.fill_frame__Action_Panel(subframe)


    def fill_frame__Action_Panel(self, frame):

        subframe = tk.Frame(frame)
        subframe.pack(fill='x')
        button = tk.Button(subframe, width=28, height=2, text="ACT",
                           command=self.act)
        button.pack(side='top')

        subframe = tk.Frame(frame)
        subframe.pack()
        spacer = tk.Label(subframe, text=" ")
        spacer.pack()

        subframe = tk.Frame(frame)
        subframe.pack(fill='x')
        radio = tk.Radiobutton(subframe, text="Click", variable=self.action_option, value=1)
        radio.pack(side="left")
        txt_label = tk.Label(subframe, text="   X:")
        txt_label.pack(side='left')
        textbox = tk.Entry(subframe, width=5, textvariable=self.click_x)
        textbox.pack(side='left')
        txt_label = tk.Label(subframe, text="   Y:")
        txt_label.pack(side='left')
        textbox = tk.Entry(subframe, width=5, textvariable=self.click_y)
        textbox.pack(side='left')
        txt_label = tk.Label(subframe, text="  ")
        txt_label.pack(side='left')
        button = tk.Button(subframe, width=8, text=message_get_coord,
                           command=lambda: self.get_coords(self.click_x, self.click_y))
        button.pack(side='left')

        subframe = tk.Frame(frame)
        subframe.pack(fill='x')
        spacer = tk.Label(subframe, text="    ")
        spacer.pack(side='left')
        checkbox = tk.Checkbutton(subframe, text="with ctrl button pressed (TBD)", variable=self.control_pressed, name='control_checkbox')  # I did not find a way to implement control-click on virtual miniwob
        checkbox.pack(side='left')

        subframe = tk.Frame(frame)
        subframe.pack()
        spacer = tk.Label(subframe, text=" ")
        spacer.pack()

        subframe = tk.Frame(frame)
        subframe.pack(fill='x')
        radio = tk.Radiobutton(subframe, text="Type", variable=self.action_option, value=2)
        radio.pack(side="left")
        txt_label = tk.Label(subframe, text="  ")
        txt_label.pack(side='left')
        textbox = tk.Entry(subframe, width=15, textvariable=self.type_string)
        textbox.pack(side='left')

        subframe = tk.Frame(frame)
        subframe.pack()
        spacer = tk.Label(subframe, text=" ")
        spacer.pack()

        subframe = tk.Frame(frame)
        subframe.pack(fill='x')
        radio = tk.Radiobutton(subframe, text="Point", variable=self.action_option, value=3)
        radio.pack(side="left")
        txt_label = tk.Label(subframe, text="   X:")
        txt_label.pack(side='left')
        textbox = tk.Entry(subframe, width=5, textvariable=self.point_x)
        textbox.pack(side='left')
        txt_label = tk.Label(subframe, text="   Y:")
        txt_label.pack(side='left')
        textbox = tk.Entry(subframe, width=5, textvariable=self.point_y)
        textbox.pack(side='left')
        txt_label = tk.Label(subframe, text="  ")
        txt_label.pack(side='left')
        button = tk.Button(subframe, width=8, text=message_get_coord,
                           command=lambda: self.get_coords(self.point_x, self.point_y))
        button.pack(side='left')

        subframe = tk.Frame(frame)
        subframe.pack()
        spacer = tk.Label(subframe, text=" ")
        spacer.pack()

        subframe = tk.Frame(frame)
        subframe.pack(fill='x')
        radio = tk.Radiobutton(subframe, text="Drag", variable=self.action_option, value=4)
        radio.pack(side="left")
        txt_label = tk.Label(subframe, text="  X1:")
        txt_label.pack(side='left')
        textbox = tk.Entry(subframe, width=5, textvariable=self.drag1_x)
        textbox.pack(side='left')
        txt_label = tk.Label(subframe, text="  Y1:")
        txt_label.pack(side='left')
        textbox = tk.Entry(subframe, width=5, textvariable=self.drag1_y)
        textbox.pack(side='left')
        txt_label = tk.Label(subframe, text="  ")
        txt_label.pack(side='left')
        button = tk.Button(subframe, width=8, text=message_get_coord,
                           command=lambda: self.get_coords(self.drag1_x, self.drag1_y))
        button.pack(side='left')

        subframe = tk.Frame(frame)
        subframe.pack(fill='x')
        txt_label = tk.Label(subframe, text="            ")
        txt_label.pack(side='left')
        txt_label = tk.Label(subframe, text="  X2:")
        txt_label.pack(side='left')
        textbox = tk.Entry(subframe, width=5, textvariable=self.drag2_x)
        textbox.pack(side='left')
        txt_label = tk.Label(subframe, text="  Y2:")
        txt_label.pack(side='left')
        textbox = tk.Entry(subframe, width=5, textvariable=self.drag2_y)
        textbox.pack(side='left')
        txt_label = tk.Label(subframe, text="  ")
        txt_label.pack(side='left')
        button = tk.Button(subframe, width=8, text=message_get_coord,
                           command=lambda: self.get_coords(self.drag2_x, self.drag2_y))
        button.pack(side='left')

        subframe = tk.Frame(frame)
        subframe.pack()
        spacer = tk.Label(subframe, text=" ")
        spacer.pack()

        subframe = tk.Frame(frame)
        subframe.pack(fill='x')
        radio = tk.Radiobutton(subframe, text="Ctrl-A", variable=self.action_option, value=11)
        radio.pack(side="left")

        subframe = tk.Frame(frame)
        subframe.pack(fill='x')
        radio = tk.Radiobutton(subframe, text="Ctrl-C", variable=self.action_option, value=12)
        radio.pack(side="left")

        subframe = tk.Frame(frame)
        subframe.pack(fill='x')
        radio = tk.Radiobutton(subframe, text="Ctrl-V", variable=self.action_option, value=13)
        radio.pack(side="left")


        subframe = tk.Frame(frame)  # spacer
        subframe.pack(expand=True, fill ='both')


    def get_coords(self, xvar, yvar):
        thread = threading.Thread(target=self.get_coords_threaded, args=(xvar, yvar))
        thread.start()

    def get_coords_threaded(self, xvar, yvar):
        # indicate that thread is running
        bg_color = self.win.cget('background')
        self.win.configure(background='black')
        self.win.update()
        virtual_miniwob_support.get_coords_threaded(self, xvar, yvar)
        self.win.configure(background=bg_color)
        self.win.lift()

    def act(self):
        virtual_miniwob_support.act(self)



    def fill_frame__conversion_radios(self, frame):
        button = tk.Button(frame, width=8, height=1, text="DIR",
                           command=lambda: os.startfile(os.path.abspath(self.conversion_folder)))
        button.pack(side='left')
        button = tk.Button(frame, width=8, height=1, text="Edit", name='edit_button',
                           command=self.edit_conversion_file)
        button.pack(side='left')
        txt_label = tk.Label(frame, text=f"   Conversion_Folder: {self.conversion_folder}", name='convert_file')
        txt_label.pack(side='left')

        # create two radio buttons and add them to the frame
        radio = tk.Radiobutton(frame, text="Processed", variable=self.df_select_option, value=2, command=self.update)
        radio.pack(side="right")
        radio = tk.Radiobutton(frame, text="Raw Data", variable=self.df_select_option, value=1, command=self.update)
        radio.pack(side="right")

    def edit_conversion_file(self):
        module_name = self.env_name.replace("-", "_")
        module_path = os.path.join(self.conversion_folder, module_name+'.py')
        if not os.path.exists(module_path):
            raise CustomException(f"Check conversion file path : {module_path}")
        os.startfile(module_path)


    def fill_frame__pandas(self, frame):

        canvas = tk.Canvas(frame, width=700, height=750)
        v_scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
        h_scrollbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL)

        h_scrollbar.pack(side='bottom', fill=tk.X)
        v_scrollbar.pack(side='right', fill=tk.Y)
        canvas.pack(side='right', fill='both', expand=True)

        canvas.config(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        v_scrollbar.config(command = canvas.yview)
        h_scrollbar.config(command = canvas.xview)

        # Create a frame to hold the grid of text labels inside the canvas
        inner_frame = tk.Frame(canvas)
        canvas.create_window(0, 0, anchor=tk.NW, window=inner_frame)

        # Bind the mouse scroll event to the canvas widget
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        # Bind the mouse enter and leave events to the canvas widget
        def on_enter(event):
            canvas.bind_all("<MouseWheel>", on_mousewheel)

        def on_leave(event):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
