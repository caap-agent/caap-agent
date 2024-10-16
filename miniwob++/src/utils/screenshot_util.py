
import ctypes
import numpy as np
from io import BytesIO
from PIL import Image
from miniwob.screenshot import get_screenshot
from miniwob.selenium_instance import SeleniumInstance


def setup():
    def __set_dpi_awareness(awareness):
        errorCode = ctypes.windll.shcore.SetProcessDpiAwareness(awareness)
        if errorCode:
            print(f"Failed to set Process DPI Awareness with errorCode: {errorCode}")
        else:
            print(f"Set Process DPI Awareness: {awareness}")


    def __get_dpi_awareness():
        awareness = ctypes.c_int()
        errorCode = ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
        if errorCode:
            print(f"Failed to get Process DPI Awareness with errorCode: {errorCode}")
        else:
            print(f"Current Process DPI Awareness: {awareness.value}")
        return awareness.value


    def __screenshot(imageFilename=None, region=None, resize=True):
        size = (region[2], region[3])

        scale_factor = None
        if resize:
            scale_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100

        region = np.array(region)
        if region is not None and scale_factor is not None:
            region = region * scale_factor
        region = tuple(map(int, region))

        img = __pyautogui_screenshot(imageFilename=None, region=region)
        if resize and scale_factor is not None and scale_factor != 1.0:
            img = img.resize(size)

        if imageFilename is not None:
            img.save(imageFilename)

        return img


    # Set DPI Awareness  (Windows 10 and 8)
    """
        Process DPI Awareness
        0 : DPI unaware
        1 : System DPI aware
        2 : Per monitor DPI aware
    """
    DPI_AWARENESS = 0
    __set_dpi_awareness(DPI_AWARENESS)
    __get_dpi_awareness()


    # Patch pyautogui.screenshot
    import pyautogui
    __pyautogui_screenshot = pyautogui.screenshot
    pyautogui.screenshot = __screenshot


def screenshot(instance: SeleniumInstance):

    img = get_screenshot(
        instance.driver,
        true_width=instance.inner_width,
        true_height=instance.inner_height,
        crop_width=instance.task_width,
        crop_height=instance.task_height,
    )
    return img
