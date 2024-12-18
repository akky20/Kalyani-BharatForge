import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import PointCloud2, LaserScan, Image
from cv_bridge import CvBridge
from bot_package.config import static_objects
from squaternion import Quaternion
import numpy as np
import torch
from pymongo import MongoClient
import math
from datetime import datetime
from bot_package.rl.train_velodyne_node import td3  # Import the TD3 implementation
from bot_package.yolo.object_detection import ObjectDetection as OD
# Utility for PointCloud2 message parsing
from bot_package.rl.point_cloud2 import point_cloud2 as pc2
from communication_msgs.srv import Liveliness, TaskAssignment, TaskCompletion


class MasterSlaveNode(Node):
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

        # ROS2 Publishers and Subscribers
        self.cmd_publisher = self.create_publisher(
            Twist, f'{self.namespace}/cmd_vel', 10)
        self.velodyne_subscriber = self.create_subscription(
            PointCloud2, f'{self.namespace}/velodyne_points', self.velodyne_callback, 10)
        self.lidar_subscriber = self.create_subscription(
            LaserScan, f'{self.namespace}/scan', self.lidar_callback, 10)
        self.camera_subscriber = self.create_subscription(
            Image, f'{self.namespace}/camera/image_raw', self.camera_callback, 10)
        self.odom_subscriber = self.create_subscription(
            Odometry, f'{self.namespace}/odom', self.odom_callback, 10)

        # Load the trained TD3 model
        # Adjust state_dim and action_dim as needed
        self.td3_model = td3(state_dim=24, action_dim=2, max_action=1)
        self.td3_model.load("td3_velodyne", "./pytorch_models")

        # Load the trained YOLO Nano object detection model
        self.model = OD(model_path)

        # Master-Slave communication
        self.master = None
        self.isMaster = False
        if self.agent_id[-1] == '1':
            self.isMaster = True
        if self.isMaster:
            self.tasks_collection = self.db['tasks']
        else:
            self.livesrv = self.create_service(
                Liveliness, agent_id, self.handle_liveliness)

        # State variables
        self.grid_size = 0.05  # 5x5 cm
        # Placeholder for processed Velodyne data
        self.velodyne_data = np.ones(20) * 10
        # Placeholder for processed LiDAR data
        self.lidar_data = np.ones(20) * 10
        self.camera_image = None
        self.current_pose = [0, 0]
        self.current_task = None  # The task currently assigned to this agent

        self.get_logger().info(
            f"Agent Node {self.agent_id} Initialized in namespace {self.namespace}")

    def handle_liveliness(self, request, response):
        response.requesterid = request.senderid
        response.receiverid = self.agent_id
        response.message = "ALIVE"
        if self.master == None:
            self.master = request.senderid
            self.live_count = 3
            self.tim = self.create_timer(15, self.ask_liveliness)
        return response

    def ask_liveliness(self):
        livereq = Liveliness.Request()
        livereq.senderid = self.agent_id
        livereq.message = "ARE YOU ALIVE?"
        self.live_count -= 1
        if self.live_count < 0:
            if int(self.agent_id[-1]) == int(self.master[-1]) + 1:
                self.isMaster = True
                self.tasks_collection = self.db['tasks']
            self.master = None
            self.tim.cancel()
        future = self.livesrv.call_async(livereq)
        future.add_done_callback(self.handle_liveness_reply)

    def handle_liveness_reply(self, future):
        result = future.result()
        if result:
            self.live_count += 1

    def velodyne_callback(self, msg):
        """Handle Velodyne data."""
        self.velodyne_data = np.ones(20) * 10  # Reset processed data
        data = list(pc2.read_points(
            msg, skip_nans=False, field_names=("x", "y", "z")))

        for point in data:
            if point[2] > -0.2:  # Ignore points below a certain height
                distance = math.sqrt(point[0]**2 + point[1]**2 + point[2]**2)
                angle = math.atan2(point[1], point[0])

                # Convert angle to index for discretization
                index = int((angle + np.pi) / (2 * np.pi / 20)) % 20
                self.velodyne_data[index] = min(
                    self.velodyne_data[index], distance)

    def lidar_callback(self, msg):
        """Handle LiDAR data."""
        self.lidar_data = np.ones(20) * 10  # Reset processed data
        ranges = np.array(msg.ranges)
        angle_min = msg.angle_min
        angle_increment = msg.angle_increment

        for i, distance in enumerate(ranges):
            if 0.2 < distance < 2.0:  # Within LiDAR range
                angle = angle_min + i * angle_increment
                x = self.current_pose[0] + distance * math.cos(angle)
                y = self.current_pose[1] + distance * math.sin(angle)
                self.update_map(x, y)

    def camera_callback(self, msg):
        """Handle camera data for object detection and labeling."""
        self.camera_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")

    def odom_callback(self, msg):
        """Update the agent's position using Odometry data."""
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        self.current_pose = (x, y)
        self.odom = msg

        self.robot_collection.update_one(
            {"robot_id": self.agent_id},
            {"$set": {"position": self.current_pose, "status": "active"}},
            upsert=True
        )

        # Check for nearby tasks
        self.execute_task()

    def execute_task(self):
        """Execute the assigned task using TD3-based navigation."""
        if not self.current_task:
            return

        goal = self.current_task["coordinates"]
        self.goal_x = goal[0]
        self.goal_y = goal[1]
        obs = self.get_robot_state()

        while True:
            action = self.td3_model.get_action(np.array(obs))
            obs, done, status = self.execute_action(action)
            if done:
                self.complete_task(status)
                break

    def get_robot_state(self, action):
        v_state = []
        v_state[:] = self.velodyne_data[:]
        laser_state = [v_state]

        # Calculate robot heading from odometry data
        self.odom_x = self.current_pose[0]
        self.odom_y = self.current_pose[1]
        quaternion = Quaternion(
            self.odom.pose.pose.orientation.w,
            self.odom.pose.pose.orientation.x,
            self.odom.pose.pose.orientation.y,
            self.odom.pose.pose.orientation.z,
        )
        euler = quaternion.to_euler(degrees=False)
        angle = round(euler[2], 4)

        # Calculate the relative angle between the robots heading and heading toward the goal
        skew_x = self.goal_x - self.odom_x
        skew_y = self.goal_y - self.odom_y
        dot = skew_x * 1 + skew_y * 0
        mag1 = math.sqrt(math.pow(skew_x, 2) + math.pow(skew_y, 2))
        mag2 = math.sqrt(math.pow(1, 2) + math.pow(0, 2))
        beta = math.acos(dot / (mag1 * mag2))
        if skew_y < 0:
            if skew_x < 0:
                beta = -beta
            else:
                beta = 0 - beta
        theta = beta - angle
        if theta > np.pi:
            theta = np.pi - theta
            theta = -np.pi - theta
        if theta < -np.pi:
            theta = -np.pi - theta
            theta = np.pi - theta

        distance = np.linalg.norm(
            [self.odom_x - self.goal_x, self.odom_y - self.goal_y]
        )

        robot_state = [distance, theta, action[0], action[1]]
        state = np.append(laser_state, robot_state)

        return state

    def execute_action(self, action):
        """Execute a continuous action provided by the TD3 model."""
        linear = float((action[0] + 1)/2)  # Scale action to [0, 1]
        angular = float(action[1])  # Angular velocity
        self.control_motion(linear, angular)
        state = self.get_robot_state(action)
        target = False
        if self.is_collision():
            done = True
            status = "failed"
        if self.is_task_completed():
            target = True
            done = True
            status = "success"
        return state, done, target, status

    def control_motion(self, linear, angular):
        """Control the robot's motion."""
        cmd = Twist()
        cmd.linear.x = float(linear)
        cmd.angular.z = float(angular)
        self.cmd_publisher.publish(cmd)

    def is_task_completed(self):
        """Check if the task is completed."""
        if self.current_pose is None or self.current_task is None:
            return False
        goal = self.current_task["coordinates"]
        distance_to_goal = math.sqrt(
            (goal[0] - self.current_pose[0]) ** 2 +
            (goal[1] - self.current_pose[1]) ** 2
        )
        return distance_to_goal < 0.2

    def is_collision(self):
        """Detect collision."""
        return np.any(self.lidar_data < 0.2) or np.any(self.velodyne_data < 0.2)

    def update_map(self, x, y):
        """Update the map in MongoDB based on grid coordinates, and handle dynamic object expiry."""
        grid_x = math.floor(x / self.grid_size)
        grid_y = math.floor(y / self.grid_size)

        # Check if the grid cell is already occupied
        existing_entry = self.map_collection.find_one(
            {"coordinates": [grid_x, grid_y]})

        # If there's no existing entry or the existing object is dynamic
        if not existing_entry or (existing_entry and existing_entry["static"] == False):
            # Turn toward the object to capture an image
            self.turn_toward(grid_x, grid_y)

            # Run object detection if we have a camera image
            if self.camera_image is not None:
                label = self.run_object_detection(self.camera_image)
                is_static = self.label_staticity(label)
                timestamp = datetime.utcnow()  # Store the current timestamp

                # Update map with the new object, including timestamp for dynamic objects
                self.map_collection.update_one(
                    {"coordinates": [grid_x, grid_y]},
                    {"$set": {
                        "obstacle": 1,
                        "label": label,
                        "static": is_static,
                        "timestamp": timestamp  # Store timestamp of object addition
                    }},
                    upsert=True
                )
                self.get_logger().info(
                    f"Added object: {label} at [{grid_x}, {grid_y}] (Static: {is_static})")

    def label_staticity(self, label):
        """Determine whether an object is static or dynamic."""
        return label in static_objects

    def turn_toward(self, grid_x, grid_y):
        """Turn the robot toward a grid cell."""
        goal_angle = math.atan2(grid_y * self.grid_size - self.current_pose[1],
                                grid_x * self.grid_size - self.current_pose[0])
        twist = Twist()
        twist.angular.z = goal_angle
        self.cmd_publisher.publish(twist)
        self.get_logger().info(f"Turning toward [{grid_x}, {grid_y}]")