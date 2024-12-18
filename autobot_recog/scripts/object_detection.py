import torch
import numpy as np
import cv2
from time import time
from ultralytics import YOLO
from bot_package.config import class_labels

class ObjectDetection:
    def __init__(self, path):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print("Using Device:", self.device)
        self.model = self.load_model(path)

    def load_model(self, path):
        model = YOLO(path)  # Path to your trained model
        model.fuse()  # Fuse model layers for optimization
        return model

    def preprocess(self, frame):
        # Resize input image (640x480) to 640x640 by padding with black edges
        h, w = frame.shape[:2]
        new_w, new_h = 640, 640

        # Calculate padding
        pad_w = (new_w - w) // 2
        pad_h = (new_h - h) // 2

        # Add padding to the image
        padded_frame = cv2.copyMakeBorder(frame, pad_h, new_h - h - pad_h, pad_w, new_w - w - pad_w, cv2.BORDER_CONSTANT, value=(0, 0, 0))

        return padded_frame

    def postprocess(self, results, frame):
        xyxys = []
        confidences = []
        class_ids = []
        class_names = []
        
        # Loop over the results and extract bounding box information
        for result in results:
            boxes = result.boxes.cpu().numpy()  # Convert boxes to numpy array
            xyxys.append(boxes.xyxy)  # Get bounding boxes (x_min, y_min, x_max, y_max)
            confidences.append(boxes.conf)  # Get confidence scores for each box
            class_ids.append(boxes.cls)  # Get the class IDs for each box

        # Output bounding box information for each detected object
        for i, box in enumerate(xyxys[0]):
            class_id = class_ids[0][i]  # Class ID of the detected object

            class_names += [class_labels[int(class_id)] if int(class_id) < len(class_labels) else "Unknown"]

        return class_names

    def predict(self, frame):
        # Preprocess image (resize and padding)
        padded_frame = self.preprocess(frame)
        
        # Perform inference
        results = self.model(padded_frame)  # Perform inference
        
        # Postprocess results (bounding boxes and other info)
        return self.postprocess(results, padded_frame)