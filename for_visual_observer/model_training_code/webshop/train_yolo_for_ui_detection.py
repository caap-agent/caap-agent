from ultralytics import YOLO
import os
os.environ["OMP_NUM_THREADS"] = "1"

# Checkpoint
checkpoint_path = '../../../../vision_model_checkpoints/base/yolov8x.pt'

yaml_path = './webshop.yaml'
training_epoch = 300
patience = 50

# Load a model
model = YOLO(checkpoint_path)
# Use the model
model.train(data=yaml_path, epochs=training_epoch, patience=patience, device=[0], box=0.9, cls=0.05, dfl=0.05)  # train the model