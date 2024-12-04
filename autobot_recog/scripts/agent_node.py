import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from sensor_msgs.msg import LaserScan, Image
from nav_msgs.msg import OccupancyGrid
from cv_bridge import CvBridge
import numpy as np
import torch
from pymongo import MongoClient
import math


class AgentNode(Node):
    def __init__(self, agent_id, namespace, model_path, mongo_uri="mongodb://localhost:27017/"):
        super().__init__(f'{namespace}_node')
        self.agent_id = agent_id
        self.namespace = namespace
        self.bridge = CvBridge()
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client['shared_database']

        # MongoDB collections
        self.map_collection = self.db['map']
        self.robot_collection = self.db['robots']
        self.tasks_collection = self.db['tasks']

        # ROS2 Publishers and Subscribers
        self.cmd_publisher = self.create_publisher(
            Twist, f'{self.namespace}/cmd_vel', 10)
        self.lidar_subscriber = self.create_subscription(
            LaserScan, f'{self.namespace}/scan', self.lidar_callback, 10)
        self.camera_subscriber = self.create_subscription(
            Image, f'{self.namespace}/turtlebot3_burger/camera/image_raw', self.camera_callback, 10)
        self.slam_subscriber = self.create_subscription(
            OccupancyGrid, f'{self.namespace}/map', self.slam_callback, 10)
        self.pose_subscriber = self.create_subscription(
            PoseStamped, f'{self.namespace}/robot_pose', self.pose_callback, 10)

        # Load the trained object detection model
        self.model = torch.load(model_path)
        self.model.eval()

        # State variables
        self.current_pose = (0, 0)
        self.obstacles = []
        self.current_image = None
        self.current_task = None  # The task currently assigned to this agent

        self.get_logger().info(
            f"Agent Node {self.agent_id} Initialized in namespace {self.namespace}")

    def lidar_callback(self, scan):
        """Handle LiDAR data for obstacle detection and avoidance."""
        ranges = np.array(scan.ranges)
        angle_min = scan.angle_min
        angle_increment = scan.angle_increment

        # Detect obstacles within a threshold distance
        self.obstacles = []
        for i, distance in enumerate(ranges):
            if 0.2 < distance < 2.0:  # Within LiDAR range
                angle = angle_min + i * angle_increment
                x = int(self.current_pose[0] + distance * np.cos(angle))
                y = int(self.current_pose[1] + distance * np.sin(angle))
                self.obstacles.append((x, y))

        # Update obstacles in MongoDB
        for obstacle in self.obstacles:
            self.map_collection.update_one(
                {"coordinates": obstacle},
                {"$set": {"obstacle": 1, "label": None, "static": None}},
                upsert=True
            )

    def camera_callback(self, msg):
        """Handle camera data for object detection and labeling."""
        self.current_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")

        # Run object detection
        detections = self.detect_objects(self.current_image)

        # Update MongoDB with detected objects
        for detection in detections:
            label, confidence, bbox = detection
            x, y, w, h = bbox
            grid_x, grid_y = self.get_grid_coordinates(x, y)

            self.map_collection.update_one(
                {"coordinates": (grid_x, grid_y)},
                {"$set": {
                    "obstacle": 1,
                    "label": label,
                    "static": self.label_staticity(label)
                }},
                upsert=True
            )

    def slam_callback(self, msg):
        """Handle SLAM updates to keep the map in sync."""
        map_data = np.array(msg.data).reshape(msg.info.height, msg.info.width)
        resolution = msg.info.resolution
        origin = msg.info.origin.position

        for i in range(map_data.shape[0]):
            for j in range(map_data.shape[1]):
                if map_data[i, j] == 100:  # Marked as an obstacle
                    x = origin.x + i * resolution
                    y = origin.y + j * resolution

                    self.map_collection.update_one(
                        {"coordinates": (x, y)},
                        {"$set": {"obstacle": 1, "label": None, "static": None}},
                        upsert=True
                    )

    def pose_callback(self, msg):
        """Update the agent's position in the MongoDB."""
        x = msg.pose.position.x
        y = msg.pose.position.y
        self.current_pose = (x, y)

        self.robot_collection.update_one(
            {"robot_id": self.agent_id},
            {"$set": {"position": self.current_pose, "status": "active"}},
            upsert=True
        )

        # Check for nearby tasks
        self.check_for_tasks()

    def detect_objects(self, image):
        """Run inference on the YOLO Nano model."""
        input_tensor = torch.from_numpy(image).permute(
            2, 0, 1).unsqueeze(0).float() / 255.0
        detections = self.model(input_tensor)
        return detections

    def get_grid_coordinates(self, x, y):
        """Convert pixel coordinates to grid coordinates."""
        return int(x / 10), int(y / 10)

    def label_staticity(self, label):
        """Determine whether an object is static or dynamic."""
        static_objects = {"box", "shelf"}
        return label in static_objects

    def check_for_tasks(self):
        """Check for tasks and assign the closest unassigned task."""
        if self.current_task is not None:
            return  # Already handling a task

        tasks = self.tasks_collection.find(
            {"status": "pending", "assigned_to": None})
        nearest_task = None
        min_distance = float('inf')

        for task in tasks:
            task_coords = task["coordinates"]
            distance = math.sqrt((self.current_pose[0] - task_coords[0])**2 +
                                 (self.current_pose[1] - task_coords[1])**2)

            if distance < min_distance:
                nearest_task = task
                min_distance = distance

        if nearest_task:
            # Assign the task to this agent
            self.tasks_collection.update_one(
                {"task_id": nearest_task["task_id"]},
                {"$set": {"assigned_to": self.agent_id, "status": "in_progress"}}
            )
            self.current_task = nearest_task
            self.get_logger().info(
                f"Assigned task {nearest_task['task_id']} at {nearest_task['coordinates']}")

    def complete_task(self):
        """Mark the current task as completed."""
        if self.current_task:
            self.tasks_collection.update_one(
                {"task_id": self.current_task["task_id"]},
                {"$set": {"status": "completed"}}
            )
            self.get_logger().info(
                f"Completed task {self.current_task['task_id']}")
            self.current_task = None

    def control_motion(self, linear, angular):
        """Control the TurtleBot's motion."""
        cmd = Twist()
        cmd.linear.x = linear
        cmd.angular.z = angular
        self.cmd_publisher.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    agent = AgentNode(agent_id="robot_1", namespace="agent_1",
                      model_path="path/to/yolo_nano_weights.pth")
    rclpy.spin(agent)
    agent.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()