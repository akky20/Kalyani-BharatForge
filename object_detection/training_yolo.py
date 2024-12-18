import cv2
import os
import os
import shutil
import random
from pathlib import Path
from ultralytics import YOLO


#Preprocessing

def preprocess_images_and_annotations(input_image_dir, input_annotation_dir, output_image_dir, output_annotation_dir):

    
    # Ensuring output directories exist
    output_image_path = Path(output_image_dir)
    output_annotation_path = Path(output_annotation_dir)
    output_image_path.mkdir(parents=True, exist_ok=True)
    output_annotation_path.mkdir(parents=True, exist_ok=True)

    crop_size = 320
    target_size = 640

    for img_file in Path(input_image_dir).glob("*"):
        if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
            # Read the image
            img = cv2.imread(str(img_file))
            h, w, _ = img.shape

            # Centrally crop the image to 320x320
            x_start = (w - crop_size) // 2
            y_start = (h - crop_size) // 2
            cropped_img = img[y_start:y_start + crop_size, x_start:x_start + crop_size]

            # Resize to 640x640 with black padding
            padded_img = cv2.copyMakeBorder(
                cropped_img,
                top=(target_size - crop_size) // 2,
                bottom=(target_size - crop_size) // 2,
                left=(target_size - crop_size) // 2,
                right=(target_size - crop_size) // 2,
                borderType=cv2.BORDER_CONSTANT,
                value=(0, 0, 0)  # Black padding
            )

            # Save the processed image
            output_image_file = output_image_path / img_file.name
            cv2.imwrite(str(output_image_file), padded_img)

            # Process the corresponding annotation file (if it exists)
            annotation_file = Path(input_annotation_dir) / (img_file.stem + ".txt")
            if annotation_file.exists():
                with open(annotation_file, "r") as ann_file:
                    annotations = ann_file.readlines()

                updated_annotations = []
                for annotation in annotations:
                    class_id, x_center, y_center, width, height = map(float, annotation.strip().split())

                    # Convert normalized values to absolute coordinates
                    abs_x_center = x_center * w
                    abs_y_center = y_center * h
                    abs_width = width * w
                    abs_height = height * h

                    # Adjust for cropping
                    abs_x_center -= x_start
                    abs_y_center -= y_start

                    # Skip boxes that are completely outside the cropped area
                    if abs_x_center < 0 or abs_x_center > crop_size or abs_y_center < 0 or abs_y_center > crop_size:
                        continue

                    # Normalize to the new 320x320 cropped image
                    norm_x_center = abs_x_center / crop_size
                    norm_y_center = abs_y_center / crop_size
                    norm_width = abs_width / crop_size
                    norm_height = abs_height / crop_size

                    # Adjust for padding to 640x640
                    norm_x_center = (norm_x_center * crop_size + (target_size - crop_size) / 2) / target_size
                    norm_y_center = (norm_y_center * crop_size + (target_size - crop_size) / 2) / target_size
                    norm_width *= crop_size / target_size
                    norm_height *= crop_size / target_size

                    # Save updated annotation
                    updated_annotations.append(f"{int(class_id)} {norm_x_center:.6f} {norm_y_center:.6f} {norm_width:.6f} {norm_height:.6f}\n")

                # Write updated annotations to a new file
                output_annotation_file = output_annotation_path / (img_file.stem + ".txt")
                with open(output_annotation_file, "w") as out_ann_file:
                    out_ann_file.writelines(updated_annotations)

                print(f"Processed and saved: {output_image_file}, {output_annotation_file}")
            else:
                print(f"Processed and saved: {output_image_file} (No annotation file found)")


input_image_dir = "/home/khyati/Obj_Detection_Bot.v4i.yolov8/orig_dataset/images"  # Directory with original images
input_annotation_dir = "/home/khyati/Obj_Detection_Bot.v4i.yolov8/orig_dataset/labels"  # Directory with YOLO annotation files
output_image_dir = "/home/khyati/Obj_Detection_Bot.v4i.yolov8/preprocessed_dataset/images"  # Directory for preprocessed images
output_annotation_dir = "/home/khyati/Obj_Detection_Bot.v4i.yolov8/preprocessed_dataset/labels"  # Directory for updated annotations

preprocess_images_and_annotations(input_image_dir, input_annotation_dir, output_image_dir, output_annotation_dir)



#Train/Val/Test Split

def split_dataset(base_dir, output_dir, train_ratio=0.7, val_ratio=0.2, test_ratio=0.1):
    # Input directories
    images_dir = os.path.join(base_dir, "images")
    labels_dir = os.path.join(base_dir, "labels")
    
    # Output directories
    train_images_dir = os.path.join(output_dir, "train/images")
    train_labels_dir = os.path.join(output_dir, "train/labels")
    val_images_dir = os.path.join(output_dir, "val/images")
    val_labels_dir = os.path.join(output_dir, "val/labels")
    test_images_dir = os.path.join(output_dir, "test/images")
    test_labels_dir = os.path.join(output_dir, "test/labels")
    
    # Create output directories
    for dir_path in [train_images_dir, train_labels_dir, val_images_dir, val_labels_dir, test_images_dir, test_labels_dir]:
        os.makedirs(dir_path, exist_ok=True)
    
    # Get all image files
    image_files = [f for f in os.listdir(images_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
    random.seed(42)
    random.shuffle(image_files)
    
    # Split dataset
    total_images = len(image_files)
    train_cutoff = int(total_images * train_ratio)
    val_cutoff = train_cutoff + int(total_images * val_ratio)
    
    train_files = image_files[:train_cutoff]
    val_files = image_files[train_cutoff:val_cutoff]
    test_files = image_files[val_cutoff:]
    
    # Helper function to copy files
    def copy_files(file_list, src_dir, dest_dir):
        for file in file_list:
            shutil.copy(os.path.join(src_dir, file), dest_dir)
    
    # Copy image and label files
    for files, img_dir, lbl_dir in [(train_files, train_images_dir, train_labels_dir),
                                    (val_files, val_images_dir, val_labels_dir),
                                    (test_files, test_images_dir, test_labels_dir)]:
        copy_files(files, images_dir, img_dir)
        for file in files:
            label_file = os.path.splitext(file)[0] + ".txt"
            if os.path.exists(os.path.join(labels_dir, label_file)):
                shutil.copy(os.path.join(labels_dir, label_file), lbl_dir)
    
    print("Dataset split complete!")
    print(f"Training set: {len(train_files)} images")
    print(f"Validation set: {len(val_files)} images")
    print(f"Test set: {len(test_files)} images")

base_dataset_dir = "/home/khyati/Obj_Detection_Bot.v4i.yolov8/preprocessed_dataset"
output_dataset_dir ="/home/khyati/Obj_Detection_Bot.v4i.yolov8"
split_dataset(base_dataset_dir, output_dataset_dir, train_ratio=0.7, val_ratio=0.2, test_ratio=0.1)



#Training

model = YOLO("/home/khyati/best.pt")  # Loading the model trained during second attempt

model.train(data='/home/khyati/Obj_Detection_Bot.v4i.yolov8/data.yaml', epochs=50, batch=16, imgsz=640, project='yolov8_training', name='my_model')


metrics = model.val()
print(metrics)






