import time
import pyautogui
from PIL import ImageTk, ImageDraw

from src.utils.customexception import CustomException
from src.utils import elements_util
from src.supports.annotator_support import sort_data
from src.utils.breakdown import Breakdown
from src import get_logger
logger = get_logger(logger_name=__file__)

TYPE_DICT = elements_util.TYPE_DICT
DICT_TYPE = {v: k for k, v in TYPE_DICT.items()}  # converted TYPE_DICT
KEYS_USED = elements_util.KEYS_USED


def refresh_model_list(self, tk):
    _clear_model_info(self)
    get_commentator_list(self, tk)
    
    # update button 'Load Models'
    _update_load_models_button(self)


def set_commentator(self, commentator: str):
    if commentator in self.commentator_list:
        self.selected_commentator.set(commentator)
    else:
        raise CustomException(
            f"Check the VISUALOBSERVER_COMMENTATOR value {commentator} is not supported")

def get_commentator_list(self, tk):
    self.commentator_list = self.screen_commentator.get_commentator_list()
    # update commentator list
    commentator_menu = self.win.children['load_models'].children['!optionmenu']
    menu = commentator_menu["menu"]
    menu.delete(0, "end")
    for comm in self.commentator_list:
        menu.add_command(label=comm, command=tk._setit(self.selected_commentator, comm))
    if len(self.commentator_list) > 0:
        self.selected_commentator.set(self.commentator_list[0])

def disable_run_models_button(self):
    self.model_loaded = False
    _update_run_models_button(self)

def load_models(self):
    try:
        commentator_model_name = self.selected_commentator.get()
        self.screen_commentator.load_models(commentator_model_name)
        self.model_loaded = True
        _update_run_models_button(self)
    except Exception as e:
        logger.info(f"{e}")
        self.update()


def read_annotator(self):
    # check if window exists
    self.ask_main_controller("open_Annotator")()
    logger.info(msg="Annotator opened!")
    Annotator = self.ask_main_controller('Annotator')
    self.img_original = Annotator.img_original.copy()
    self.element_list = Annotator.element_list.copy()

    self.element_desc_list = []
    for idx, element in enumerate(self.element_list):
        desc = elements_util.to_string(element)
        element_desc = f" element_{idx+1}: {desc}"
        self.element_desc_list.append(element_desc)
    
    update_list_box(self)
    draw_img_original(self)
    self.update()


def import_screen(self, delay=None):
    # check if window exists
    self.ask_main_controller('open_MiniWob')()
    logger.info(msg='MiniWob opened!')

    if delay is not None:
        time.sleep(delay)
    screen_region = self.ask_main_controller('miniwob_screen_region')
    self.img_original = pyautogui.screenshot(region=screen_region)
    self.draw_img_original()

    # Clear element_list
    self.element_list = []
    self.element_desc_list = []
    update_list_box(self)


def draw_img_original(self):

    # resize
    width, height = self.img_original.size
    width = width * self.multiplier
    height = height * self.multiplier
    img_enlarged = self.img_original.resize((width, height))
    tk_image1 = ImageTk.PhotoImage(img_enlarged)
    tk_image2 = ImageTk.PhotoImage(img_enlarged)
    self.tk_image1 = tk_image1
    self.tk_image2 = tk_image2

    # Image-1
    frame = self.win.children['two_image_frame']
    img_label = frame.children['subframe1'].children['img1']
    img_label.config(image=self.tk_image1, height=height+8)

    # Image-2
    img_label = frame.children['subframe2'].children['img2']
    img_label.config(image=self.tk_image2, height=height+8)

def run_models(self):
    if self.img_original is None:
        return
    try:
        
        width, height = self.img_original.size
        t_width = width * self.multiplier
        t_height = height * self.multiplier
        self.img_enlarged = self.img_original.resize((t_width, t_height)).copy()

        # Send the target image to Screen Commentator and receive element-wise descriptions.
        results = self.screen_commentator.run_models(self.img_enlarged, self.multiplier)
        
        self.element_list = []
        for generated_data in results:
            generated_data['type'] = DICT_TYPE[generated_data['type']]
            # Breakdown scrollbar_v
            if generated_data['type'] == 40:
                sub_element_list = Breakdown(generated_data, tmp_origin_image_path)
                for sub_element in sub_element_list:
                    self.element_list.append(sub_element)
            else:
                self.element_list.append(generated_data)
        self.element_list = sort_data(self.element_list)
        self.element_desc_list = []
        for idx, element in enumerate(self.element_list):
            desc = elements_util.to_string(element)
            element_desc = f" element_{idx+1}: {desc}"
            self.element_desc_list.append(element_desc)
        self.selected = -1
        update_list_box(self)
        self.update()
    except Exception as e:
        logger.info(f"On run_models : {e}")
        self.update()
    

def _clear_model_info(self):
    self.commentator_list = []
    self.selected_commentator.set('None')
    self.win.children['load_models'].children['!optionmenu']['menu'].delete(0, "end")
    _update_load_models_button(self)

def _update_load_models_button(self):
    if len(self.commentator_list) == 0:
        self.win.children['load_models'].children['load_models_button'].configure(state='disabled')
    else:
        self.win.children['load_models'].children['load_models_button'].configure(state='active')
    _update_run_models_button(self)


def update_list_box(self):
    # List_Box
    #####################################################
    listbox_frame = self.win.children['listbox_frame']
    listbox = listbox_frame.children['!listbox']
    listbox.delete(0, 'end')
    for element_desc in self.element_desc_list:
        listbox.insert('end', element_desc)

def _update_run_models_button(self):
    if self.model_loaded:
        if len(self.commentator_list) == 0:
            self.win.children['operations'].children['subframe2'].children['subsub'].children['run_models_button'].configure(state='disabled')
        else:
            self.win.children['operations'].children['subframe2'].children['subsub'].children['run_models_button'].configure(state='active')
    else:
        self.win.children['operations'].children['subframe2'].children['subsub'].children['run_models_button'].configure(state='disabled')

def update(self):

    # Buttons
    #####################################################
    if len(self.commentator_list) == 0:
        self.win.children['load_models'].children['!optionmenu']["menu"].delete(0, "end")
    _update_load_models_button(self)

    # Images
    #####################################################
    width, height = self.img_original.size
    width = width * self.multiplier
    height = height * self.multiplier
    img_enlarged = self.img_original.resize((width, height)).copy()

    draw = ImageDraw.Draw(img_enlarged)
    for id, element in enumerate(self.element_list):
        (x1, y1, x2, y2) = element['coords']

        x1 = x1 * self.multiplier
        x2 = x2 * self.multiplier
        y1 = y1 * self.multiplier
        y2 = y2 * self.multiplier

        if id == self.selected:
            draw.rectangle((x1, y1, x2, y2), outline='red', width=5)
        else:
            draw.rectangle((x1, y1, x2, y2), outline='red', width=2)
        
        if 'checked' in element.keys() and element['checked'] == 'True':
            draw.rectangle((x1, y1, x2, y2), outline=(0,255,0), width=3)
        if 'focused' in element.keys() and element['focused'] == 'True':
            draw.rectangle((x1, y1, x2, y2), outline=(0,255,175), width=3)
        if 'highlighted' in element.keys() and element['highlighted'] == 'True':
            draw.rectangle((x1, y1, x2, y2), outline=(0,255,255), width=3)

    tk_image2 = ImageTk.PhotoImage(img_enlarged)
    self.tk_image2 = tk_image2

    # Image-2
    frame = self.win.children['two_image_frame']
    img_label = frame.children['subframe2'].children['img2']
    img_label.config(image=self.tk_image2, height=height+8)
