#!/usr/bin/env python3
import os
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class ImageSaver(Node):
    def __init__(self, save_interval=0.5):
        super().__init__('image_saver')
        
        # Create a subscription to the image topic
        self.bridge = CvBridge()
        self.image_sub = self.create_subscription(
            Image, 
            '/turtlebot3_burger/camera/image_raw', 
            self.image_callback, 
            10  # QoS depth
        )
        
        # Parameters
        self.save_interval = save_interval
        self.last_save_time = 0
        self.save_directory = "dataset"
        self.image_count = 0
        
        # Create save directory if it doesn't exist
        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)
        
        # Optional: Log that the node is ready
        self.get_logger().info('Image Saver Node initialized.')

    def image_callback(self, msg):
        current_time = time.time()
        
        # Check if enough time has passed since last save
        if current_time - self.last_save_time >= self.save_interval:
            try:
                # Convert ROS image message to OpenCV image
                cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
                
                # Generate image filename
                image_path = os.path.join(self.save_directory, f"image_{self.image_count:d}.jpg")
                
                # Save the image
                cv2.imwrite(image_path, cv_image)
                
                # Log the save
                self.get_logger().info(f"Saved image {image_path}")
                
                # Increment counters
                self.image_count += 1
                self.last_save_time = current_time
            
            except Exception as e:
                self.get_logger().error(f"Error saving image: {str(e)}")

def main(args=None):
    # Initialize ROS 2 Python client library
    rclpy.init(args=args)
    
    # Create the node
    image_saver = ImageSaver(save_interval=0.5)
    
    # Spin the node
    try:
        rclpy.spin(image_saver)
    except KeyboardInterrupt:
        image_saver.get_logger().info('Node stopped cleanly.')
    finally:
        # Shutdown the node
        image_saver.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()