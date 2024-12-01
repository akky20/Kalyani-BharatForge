import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        # Launch the TurtleBot3 with Gazebo
        Node(
            package='autobot_recog',
            executable='',
            name='turtlebot3_world',
            output='screen',
            parameters=[{'use_sim_time': True}],
        ),
        
        # Launch the RealSense Camera
        Node(
            package='realsense2_camera',
            executable='realsense2_camera_node',
            name='realsense2_camera_node',
            output='screen',
            parameters=[{'use_sim_time': True}],
        ),
    ])
