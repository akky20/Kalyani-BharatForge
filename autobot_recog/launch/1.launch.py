import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os
from launch.conditions import IfCondition 

def generate_launch_description():
    return LaunchDescription([
        # Launch Gazebo with TurtleBot3 model
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=['-entity', 'turtlebot3_with_camera',
                       '-file', os.path.join(
                           get_package_share_directory('autobot_recog'), 'urdf', 'turtlebot3_camera.urdf')],
            output='screen',
        ),

        # Launch the RealSense Camera Plugin
        Node(
            package='realsense2_camera',
            executable='realsense2_camera_node',
            name='realsense2_camera_node',
            output='screen',
            parameters=[{'use_sim_time': True}],
        ),

        # Optionally, spawn the controller for the robot's movement
        # Node(
        #     package='turtlebot3_teleop',
        #     executable='turtlebot3_teleop_key',
        #     name='teleop_keyboard',
        #     output='screen',
        # ),
    ])
