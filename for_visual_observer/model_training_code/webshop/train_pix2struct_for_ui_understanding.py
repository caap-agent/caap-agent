from matplotlib import pyplot as plt
import os
os.environ["NO_PROXY"] = "http://localhost,http://0.0.0.0,localhost,127.0.0.1"

from PIL import Image, ImageDraw, ImageFilter

import json

import torch

import random
random.seed(0)

import numpy as np

from transformers import AutoProcessor, Pix2StructForConditionalGeneration
import datetime

from accelerate import Accelerator


#############################
# Set TRAIN
TRAIN_EPOCHS = 30
# Set for training
MAX_PATCHES = 2080
MAX_TXT_LENGTH = 500

# Set for data generation
num_augmentation = 4
DARKNESS = 40

TRAIN_BATCH_SIZE = 1
TEST_BATCH_SIZE = 1

pretrained_model_path = '../../../../vision_model_checkpoints/base/hub/hub_google'

training_dataset_path = '../../datasets/webshop_dataset/commentator_labels/train2024'
validation_dataset_path = '../../datasets/webshop_dataset/commentator_labels/valid2024'
#############################
#############################

def print_timestamp():
    now = datetime.datetime.now()
    print(f"{now.year}_{now.month}_{now.day}_{now.hour}_{now.minute}_{now.microsecond}")

    
    
## Load Original Annotation Image with Mask for each element
def get_highlighted_cropped_image(gt_image, gt_label, darkness):
    width, height = gt_image.size

    x1, y1, x2, y2 = gt_label['coords']
        
    new_img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    new_img.paste(gt_image, (0, 0))
    mask = Image.new('RGBA', (width, height), (0, 0, 0, darkness))
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

def get_highlighted_image_from_image_path(gt_image_path, gt_label, darkness=100):
    gt_image = Image.open(gt_image_path)
    new_img = get_highlighted_cropped_image(gt_image, gt_label, darkness)    
    return new_img

#################################
## Data Augmentation Processing #
def get_chanel_shuffled_image_from_np_array(np_image):
    index_list = list(range(3))
    
    while index_list == list(range(3)):
        random.shuffle(index_list)

    tmp = np_image[:, :, index_list[0]].copy()
    np_image[:, :, index_list[0]] = np_image[:, :, index_list[1]].copy()
    np_image[:, :, index_list[1]] = np_image[:, :, index_list[2]].copy()
    np_image[:, :, index_list[2]] = tmp

    target_image = Image.fromarray(np_image)
    return target_image

def get_shift_color_space_image_from_np_array(np_image):
    iterate_number = random.randint(1,2)
    for _ in range(iterate_number):
        random_chanel = random.randint(0,2)
        np_image[:, :, random_chanel] = (np_image[:, :, random_chanel] + random.randint(0, 128) ) % 256
    
    return Image.fromarray(np_image)

def get_salt_and_pepper_image_from_np_array(np_image):
    size = np_image[:, :, 0].shape
    salt_n_pepper = np.random.uniform(0, 500, size)
    test_salt_img = np_image.copy()
    test_salt_img[salt_n_pepper<2] = [0,0,0]
    test_salt_img[salt_n_pepper<1] = [255,255,255]
    
    return Image.fromarray(test_salt_img)
# Data Augmentation Processing ##
#################################



def get_highlighted_image_with_random_augmented_filter(gt_image_path, gt_label, darkness=50):
    # x1, y1, x2, y2 random offset -2 ~ 2
    offset=[random.randint(-2,1),random.randint(-2,1),random.randint(-1,2),random.randint(-1,2),random.randint(-10,10)]
    
    # load original image
    original_image = Image.open(gt_image_path)
    gt_image = original_image.copy()
    np_original_image = np.array(original_image)
    
    # Convert random image
    np_original_image = np.array(gt_image)    
    
    image_processing_idx = random.randint(0,3)
    # Salt & Pepper
    if image_processing_idx == 0:
        gt_image = get_salt_and_pepper_image_from_np_array(np_original_image)
    # Unsharp
    elif image_processing_idx == 1:
        value = random.randint(1,20)
        gt_image = gt_image.filter(ImageFilter.UnsharpMask(value*10))
    # Gaussian blur
    elif image_processing_idx == 2:
        value = np.random.uniform(0.2, 1.0)
        gt_image = gt_image.filter(ImageFilter.GaussianBlur(value))
        
    x1, y1, x2, y2 = gt_label['coords']
    
    x1 += offset[0]
    y1 += offset[1]
    x2 += offset[2]
    y2 += offset[3]
    # 50 is default value
    darkness = darkness + offset[4]
    darkness = max(10, darkness)
    
    if x1 < x2 and y1 < y2:
        gt_label['coords'] = [x1, y1, x2, y2]
    new_img = get_highlighted_cropped_image(gt_image, gt_label, darkness)
    
    return new_img
    
def read_dataset(data_root, num_augmentation=1, is_for_train=False):
    max_txt_size = 0

    data = []
    annotation_label_list = [f for f in os.listdir(data_root) if '_annotation' in f]
    base_path, end_folder = os.path.split(data_root)
    base_path, _  = os.path.split(base_path)
    image_root_path = os.path.join(base_path, 'images', end_folder)
    for annotation_file_name in annotation_label_list:
        annotation_file_fullpath = os.path.join(data_root, annotation_file_name)
        gt_file_name = annotation_file_name.replace('_annotation', '')
        gt_file_fullpath = os.path.join(data_root, gt_file_name)

        annotation_data_list = []
        with open(annotation_file_fullpath, 'r') as f:
            annotation_data_list = [json.loads(data.strip()) for data in f.readlines()]

        gt_data_list = []
        with open(gt_file_fullpath, 'r') as f:
            gt_data_list = [data.strip() for data in f.readlines()]
                
        target_image_fullpath = os.path.join(image_root_path, gt_file_name.replace('.txt', '.png'))
        
        if is_for_train:
            for idx, annotation_data in enumerate(annotation_data_list):
                gt_label = gt_data_list[idx]

                new_data = {}
                new_data['target_image_fullpath'] = target_image_fullpath
                new_data['annotation_data'] = annotation_data
                new_data['augmentation_flag'] = False
                new_data['text'] = gt_label

                max_txt_size = max(max_txt_size, len(new_data['text']))
                data.append(new_data)

            for _ in range(num_augmentation):
                for idx, annotation_data in enumerate(annotation_data_list):
                    gt_label = gt_data_list[idx]

                    new_data = {}
                    new_data['target_image_fullpath'] = target_image_fullpath
                    new_data['annotation_data'] = annotation_data
                    new_data['augmentation_flag'] = True
                    new_data['text'] = gt_label

                    max_txt_size = max(max_txt_size, len(new_data['text']))
                    data.append(new_data)
        else:
            # Original GT            
            for idx, annotation_data in enumerate(annotation_data_list):

                gt_label = gt_data_list[idx]

                new_data = {}
                new_data['target_image_fullpath'] = target_image_fullpath
                new_data['annotation_data'] = annotation_data
                new_data['augmentation_flag'] = False
                new_data['text'] = gt_label

                max_txt_size = max(max_txt_size, len(new_data['text']))


                data.append(new_data)
                    
    print(f"data count : {len(data)}")
    return data, max_txt_size
    

accelerator = Accelerator()
device = accelerator.device

gen_train_data, max_txt_size = read_dataset(training_dataset_path, num_augmentation, True)
MAX_TXT_LENGTH = max(MAX_TXT_LENGTH, max_txt_size)
gen_valid_data, max_txt_size = read_dataset(validation_dataset_path, num_augmentation)
MAX_TXT_LENGTH = max(MAX_TXT_LENGTH, max_txt_size)
print("==="*30)
print(f"Train Epochs : {TRAIN_EPOCHS} ")
print(f"MAX_TXT_LENGTH : {MAX_TXT_LENGTH} :::: for_training {len(gen_train_data)}, for_valid {len(gen_valid_data)}")
print("---"*30)

##### ImageCaptioningDataset
from torch.utils.data import Dataset, DataLoader



class ImageCaptioningDataset(Dataset):
    def __init__(self, dataset, processor, train, darkness=DARKNESS):
        self.dataset = dataset
        self.processor = processor
        self.is_train = train
        self.darkness = darkness

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        item = self.dataset[idx]
        target_image_fullpath = item['target_image_fullpath']
        annotation_data = item['annotation_data']
        if self.is_train:
            # Augmentation flag
            augmentation_flag = item['augmentation_flag']
            
            if augmentation_flag == False:
                item['image'] = get_highlighted_image_from_image_path(target_image_fullpath, annotation_data, self.darkness)
            else:
                item['image'] = get_highlighted_image_with_random_augmented_filter(target_image_fullpath, annotation_data, self.darkness)
        else:
            item['image'] = get_highlighted_image_from_image_path(target_image_fullpath, annotation_data, self.darkness)
        
        
        encoding = self.processor(images=item["image"], return_tensors="pt", add_special_tokens=True, max_patches=MAX_PATCHES)
        
        encoding = {k:v.squeeze() for k,v in encoding.items()}
        encoding["text"] = item["text"]
        return encoding

    


# pretrained_model_path = '../hub/hub_google'
processor = AutoProcessor.from_pretrained(pretrained_model_path)
model = Pix2StructForConditionalGeneration.from_pretrained(pretrained_model_path)


def collator(batch):
    new_batch = {"flattened_patches":[], "attention_mask":[]}
    texts = [item["text"] for item in batch]

    text_inputs = processor(text=texts, padding="max_length", return_tensors="pt", add_special_tokens=True, max_length=MAX_TXT_LENGTH)

    new_batch["labels"] = text_inputs.input_ids

    for item in batch:
        new_batch["flattened_patches"].append(item["flattened_patches"])
        new_batch["attention_mask"].append(item["attention_mask"])

    new_batch["flattened_patches"] = torch.stack(new_batch["flattened_patches"])
    new_batch["attention_mask"] = torch.stack(new_batch["attention_mask"])

    return new_batch


train_dataset = ImageCaptioningDataset(gen_train_data, processor, True)
train_dataloader = DataLoader(train_dataset, shuffle=True, batch_size=TRAIN_BATCH_SIZE, collate_fn=collator)

test_dataset = ImageCaptioningDataset(gen_valid_data, processor, False)
test_dataloader = DataLoader(test_dataset, shuffle=False, batch_size=TEST_BATCH_SIZE, collate_fn=collator)


optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5)

# make result folder
if accelerator.is_main_process:    
    now = datetime.datetime.now()
    print(f"{now.year}_{now.month}_{now.day}_{now.hour}_{now.minute}_{now.microsecond}")
    
    result_folder = 'results/webshop'
    time_dataformat = f"{now.year}_{now.month}_{now.day}_{now.hour}_{now.minute}_{now.microsecond}"
    result_folder = os.path.join(result_folder, time_dataformat)
    os.makedirs(result_folder, exist_ok=True)


def test_data(model, dataloader, draw_image=False, num_test=0):
    model.eval()

    for idx, batch in enumerate(dataloader):
        print(f"test idx [{idx:02d}]")
        labels = batch.pop("labels").to(device)
        flattened_patches = batch.pop("flattened_patches").to(device)
        attention_mask = batch.pop("attention_mask").to(device)

        with torch.no_grad():
            generated_ids = model.generate(flattened_patches=flattened_patches,
                            attention_mask=attention_mask,
                            max_length=MAX_TXT_LENGTH)
            
        label_text = processor.batch_decode(labels, skip_special_tokens=True)[0]
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        if draw_image:
            image = gen_valid_data[idx]['image']
            plt.imshow(image)  
            plt.show()
          
        print(f"[{idx:02d}] Ground truth    : \n{label_text}")
        print("-"*100)
        print(f"[{idx:02d}] Generated output: \n{generated_text}")
        print("="*100)
        
        if num_test>0 and idx>=num_test:
            print(f"if break {idx}>={num_test}")
            break 

########################################################################
# Train the model
def train(model_a, model, optimizer):
    
    if accelerator.is_main_process:
        checkpoint_dict = {
            'epoch': 0,
            'model_dict': model.state_dict(),
        }
        torch.save(checkpoint_dict, '{}/checkpoint-{}.pt'.format(result_folder, 0))
    
    for epoch in range(1, TRAIN_EPOCHS+1):
        for idx, batch in enumerate(train_dataloader):
            model_a.train()

            labels = batch.pop("labels")
            flattened_patches = batch.pop("flattened_patches")
            attention_mask = batch.pop("attention_mask")

            outputs = model_a(flattened_patches=flattened_patches,
                            attention_mask=attention_mask,
                            labels=labels)

            loss = outputs.loss

            if ( epoch == 1 and idx%100==0 ) or idx%500==0:
                print(f"Epoch: {epoch}/{TRAIN_EPOCHS}, idx:{idx}, Loss: {loss.item()}")

            #loss.backward()
            accelerator.backward(loss)
            
            optimizer.step()
            optimizer.zero_grad()

        if accelerator.is_main_process:
            test_data(model, test_dataloader, False, 20)
            
        if accelerator.is_main_process:
            checkpoint_dict = {
                'epoch': epoch,
                'model_dict': model.state_dict(),
            }
            torch.save(checkpoint_dict, '{}/checkpoint-{}.pt'.format(result_folder, epoch))
            
            print_timestamp()
            print("{}/checkpoint-{}.pt saved".format(result_folder, epoch))            
    
    if accelerator.is_main_process:
        checkpoint_dict = {
            'epoch': TRAIN_EPOCHS,
            'model_dict': model.state_dict(),
        }
        torch.save(checkpoint_dict, '{}/checkpoint-{}.pt'.format(result_folder, TRAIN_EPOCHS))        
        print("{}/checkpoint-{}.pt saved".format(result_folder, TRAIN_EPOCHS))

model_a, optimizer, train_dataloader, test_dataloader = accelerator.prepare(
    model, optimizer, train_dataloader, test_dataloader
)

train(model_a, model, optimizer)

if accelerator.is_main_process:
    test_data(model, test_dataloader, False, 0)