from transformers import AutoProcessor, Pix2StructForConditionalGeneration
from PIL import Image, ImageDraw
from ultralytics import YOLO

import json
import math
import os

batch_input_image_size = 1
MAX_PATCHES = 2080
MAX_TXT_LENGTH = 500

def _surround_bouding_bbox(bbox_list):
    """
    Calculates the bounding box that surrounds a list of bounding boxes.
    Args:
        bbox_list: A list of bounding boxes represented as tuples of (x1, y1, x2, y2).
    Returns:
        A single bounding box represented as a tuple (x1, y1, x2, y2) that surrounds all provided bounding boxes.
    """
    sx1, sy1, sx2, sy2 = bbox_list[0]
    for bbox in bbox_list[0:]:
        sx1 = min(sx1, bbox[0])
        sy1 = min(sy1, bbox[1])
        sx2 = max(sx2, bbox[2])
        sy2 = max(sy2, bbox[3])
    return [sx1, sy1, sx2, sy2]

def _compute_iou(box1, box2):
    """
    Computes the Intersection over Union (IoU) between two bounding boxes.
    Args:
        box1: A tuple of (x1, y1, x2, y2).
        box2: A tuple of (x1, y1, x2, y2).
    Returns:
        The IoU between the two bounding boxes.
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    if x2 <= x1 or y2 <= y1:
        return 0.0

    intersection = (x2 - x1) * (y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    iou = intersection / float(area1 + area2 - intersection)
    return iou

def _get_boxes_without_duplicate(bbox_list, iou_threshold=0.6):
    merged_bbox = []
    skip_idx_list = []
    for p_box_id, pin_box in enumerate(bbox_list):
        if p_box_id in skip_idx_list:
            continue
        else:
            skip_idx_list.append(p_box_id)
        m_condidate_bbox = [pin_box]
        for s_box_id, s_box in enumerate(bbox_list):        
            if s_box_id in skip_idx_list:
                continue

            iou = _compute_iou(pin_box, s_box)
            if iou > iou_threshold:
                skip_idx_list.append(s_box_id)
                m_condidate_bbox.append(s_box)
        merged_bbox.append(_surround_bouding_bbox(m_condidate_bbox))
    return merged_bbox

def _get_highlighted_cropped_image(img, bbox, DARKNESS=100):
    width = img.width
    height = img.height
    x1, y1, x2, y2 = bbox
    
    new_img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    new_img.paste(img, (0, 0))
    mask = Image.new('RGBA', (width, height), (0, 0, 0, DARKNESS))
    draw = ImageDraw.Draw(mask)
    draw.rectangle((x1, y1, x2, y2), fill=(255, 255, 255, 0))
    new_img.paste((200, 0, 0, 100), mask=mask)
    draw = ImageDraw.Draw(new_img)
    linewidth = 2
    offset = linewidth+1
    draw.rectangle((x1-offset, y1-offset, x2+offset, y2+offset), outline=(0, 0, 200, 200), width=linewidth)
    
    box_width = x2 - x1
    box_height = y2 - y1
    c_x1 = max(0, x1 - 0.5 * box_width)
    c_x2 = min(width, x2 + 0.5 * box_width)
    c_y1 = max(0, y1 - 0.5 * box_height)
    c_y2 = min(height, y2 + 0.5 * box_height)
    
    cropped_img = new_img.crop((c_x1, c_y1, c_x2, c_y2))
    
    return cropped_img


class ScreenCommentator:
    def __init__(self, saved_chechpoint_root_path):
        self.device = 'cpu'
        
        # Screen commenatator checkpoints path
        checkpoint_base_path = os.path.join(saved_chechpoint_root_path, 'webshop')

        # Set Detector & Commentator checkpoint base
        self.detector_checkpoints_base = os.path.join(checkpoint_base_path, 'yolo_model')
        self.commentator_checkpoint_base = os.path.join(checkpoint_base_path, 'pix2struct_model')

        self.commentator_model = None
        self.commentator_processor = None
        self.detector_model = None


    def get_commentator_list(self):
        return os.listdir(self.commentator_checkpoint_base)


    def _load_detector_models(self):
        checkpoint_path = os.path.join(self.detector_checkpoints_base, 'model_x.pt')
        self.detector_model = YOLO(checkpoint_path)

    def _load_commentator_model(self, model_name):
        pretrained_path = os.path.join(self.commentator_checkpoint_base, model_name)
        self.commentator_model = Pix2StructForConditionalGeneration.from_pretrained(pretrained_path, device_map=self.device)
        self.commentator_processor = AutoProcessor.from_pretrained(pretrained_path)


    def load_models(self, model_name):
        self._load_detector_models()
        self._load_commentator_model(model_name)

    
    def _get_bbox_from_object_detectors(self, image, width, height):
        # Each detector predict bboxes
        results = self.detector_model.predict(image, conf=0.7, iou=0.4, verbose=False)
        result_list = results[0].boxes.xyxyn.tolist()

        result_bbox_list = list()
        for bbox in result_list:
            original_bbox = [bbox[0] * width, bbox[1] * height, bbox[2] * width, bbox[3] * height]
            result_bbox_list.append(original_bbox)
        return result_bbox_list


    def run_models(self, target_image, multiplier):
        # Screenshot image from ROI
        width, height = target_image.size
        # Get weighted boxes fusion results from detected bboxes using YOLO v8n, v8m, v8x
        bbox_list = self._get_bbox_from_object_detectors(target_image, width, height)
        # Remove duplicated bboxes. in this case, it happens very rarely, but bboxes had different classes.
        clear_bbox_list = _get_boxes_without_duplicate(bbox_list, 0.8)
        
        if len(clear_bbox_list) == 0:
            return []
        
        # Make highlighted image for Commentator
        input_img_list = []
        for bbox in clear_bbox_list:
            input_img_list.append(_get_highlighted_cropped_image(target_image, bbox))

        generated_texts_list = list()
        inference_round = math.ceil(len(input_img_list)/batch_input_image_size)
        for ir in range(inference_round):
            start_index = ir*batch_input_image_size
            batch_image_list = input_img_list[start_index:start_index+batch_input_image_size]
            inputs = self.commentator_processor(images=batch_image_list, return_tensors="pt", max_patches=MAX_PATCHES)
            generated_ids = self.commentator_model.generate(**inputs, max_new_tokens=MAX_TXT_LENGTH)
            generated_texts = self.commentator_processor.batch_decode(generated_ids, skip_special_tokens=True)

            generated_texts_list.extend(generated_texts)

        # Since the sentence generated by Commentator does not contian coordinate values, so add them.
        generated_results = []
        for data_idx, data in enumerate(generated_texts_list):
            loaded_data = json.loads(data)
            loaded_data['coords'] = [int(coord/multiplier) for coord in clear_bbox_list[data_idx]]
            generated_results.append(loaded_data)

        return generated_results