import gym
from gym import spaces
import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
import random
import math

class GazeboRLGoalEnv(gym.Env):
    def __init__(self, map_bounds=(10, 10), goal_count=5, goal_tolerance=0.4):
        super(GazeboRLGoalEnv, self).__init__()

        # Initialize ROS2 Node
        rclpy.init()
        self.node = rclpy.create_node('gazebo_rl_env')
        
        # Define ROS2 Publishers and Subscribers
        self.cmd_publisher = self.node.create_publisher(Twist, '/cmd_vel', 10)
        self.scan_subscriber = self.node.create_subscription(LaserScan, '/scan', self.lidar_callback, 10)
        self.odom_subscriber = self.node.create_subscription(Odometry, '/odom', self.odom_callback, 10)

        # Map Bounds and Goal Setup
        self.map_bounds = map_bounds
        self.goal_count = goal_count
        self.goal_tolerance = goal_tolerance
        self.current_pose = None
        self.lidar_data = None
        self.goals = self.generate_random_goals()

        # RL Environment Setup
        self.action_space = spaces.Discrete(5)  # [Stop, Forward, Turn Left, Turn Right, Reverse]
        self.observation_space = spaces.Box(low=0, high=1, shape=(361,), dtype=np.float32)

        # Simulation Parameters
        self.max_steps = 500
        self.step_count = 0
        self.current_goal = None

    def seed(self, seed=None):
        """Set the random seed for reproducibility."""
        self.np_random, seed = gym.utils.seeding.np_random(seed)
        return [seed]

    def generate_random_goals(self):
        """Generate random goal points within the map bounds."""
        goals = []
        for _ in range(self.goal_count):
            goal_x = random.uniform(0, self.map_bounds[0])
            goal_y = random.uniform(0, self.map_bounds[1])
            goals.append([goal_x, goal_y])
        return goals

    def reset(self):
        """Reset the environment: spawn robot and choose new random goal."""
        self.step_count = 0

        # Choose a random goal
        self.current_goal = random.choice(self.goals)

        # Reset robot pose and sensor data
        self.current_pose = None
        self.lidar_data = None
        
        # Wait for sensor data to initialize
        for _ in range(10):
            rclpy.spin_once(self.node)

        # Return the initial observation
        return self.get_observation()

    def step(self, action):
        """Execute one step in the environment."""
        self.step_count += 1

        # Execute the selected action
        self.execute_action(action)

        # Wait for sensors to update
        rclpy.spin_once(self.node)

        # Compute observation, reward, and done status
        observation = self.get_observation()
        reward = self.compute_reward()
        done = self.check_done()

        return observation, reward, done, {}

    def execute_action(self, action):
        """Execute a single action."""
        if action == 0:
            self.send_velocity(0.0, 0.0)  # Stop
        elif action == 1:
            self.send_velocity(0.1, 0.0)  # Forward
        elif action == 2:
            self.send_velocity(0.0, 0.5)  # Turn Left
        elif action == 3:
            self.send_velocity(0.0, -0.5)  # Turn Right
        elif action == 4:
            self.send_velocity(-0.1, 0.0)  # Reverse

    def lidar_callback(self, msg):
        """Handle LiDAR data."""
        self.lidar_data = np.array(msg.ranges)

    def odom_callback(self, msg):
        """Handle odometry data."""
        self.current_pose = (
            msg.pose.pose.position.x,
            msg.pose.pose.position.y
        )

    def get_observation(self):
        """Get the observation (LiDAR + distance to goal)."""
        if self.lidar_data is None or self.current_pose is None:
            return np.zeros(361, dtype=np.float32)

        # Compute distance to the current goal
        distance_to_goal = self.compute_distance_to_goal()
        
        # Normalize LiDAR data
        lidar_normalized = np.clip(self.lidar_data / 10.0, 0, 1)  # Normalize LiDAR range to [0, 1]
        
        return np.append(lidar_normalized, distance_to_goal)

    def compute_reward(self):
        """Compute reward: based on distance to goal and collisions."""
        if self.check_collision():
            return -1000  # Penalize collisions
        if self.check_goal_reached():
            return 100  # Reward for reaching the goal

        # Reward for reducing distance to goal
        return -self.compute_distance_to_goal()

    def check_done(self):
        """Check if the episode is done."""
        return self.check_collision() or self.check_goal_reached() or self.step_count >= self.max_steps

    def check_collision(self):
        """Check if there is a collision using LiDAR data."""
        return self.lidar_data is not None and np.any(self.lidar_data < 0.35)

    def check_goal_reached(self):
        """Check if the robot has reached the goal."""
        distance_to_goal = self.compute_distance_to_goal()
        return distance_to_goal < self.goal_tolerance

    def compute_distance_to_goal(self):
        """Compute the Euclidean distance to the current goal."""
        if self.current_pose is None or self.current_goal is None:
            return float('inf')
        return math.sqrt(
            (self.current_pose[0] - self.current_goal[0]) ** 2 +
            (self.current_pose[1] - self.current_goal[1]) ** 2
        )

    def send_velocity(self, linear, angular):
        """Send velocity commands to the robot."""
        twist = Twist()
        twist.linear.x = float(linear)
        twist.angular.z = float(angular)
        self.cmd_publisher.publish(twist)

    def close(self):
        """Shutdown ROS2 and clean up."""
        rclpy.shutdown()