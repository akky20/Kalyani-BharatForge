#!/usr/bin/env python3
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os
from launch.conditions import IfCondition  # Import IfCondition

def generate_launch_description():
    # Path to the robot description file
    model_path = os.path.join(
        get_package_share_directory('realsense2_description'),
        'urdf/test_d435_camera.urdf.xacro'
    )

    # Path to the Gazebo launch file
    gazebo_launch_path = os.path.join(
        get_package_share_directory('autobot_recog'),
        'launch/gazebo.launch.py'
    )

    # Path to the RViz config file
    rviz_config_path = os.path.join(
        get_package_share_directory('realsense2_description'),
        'rviz/urdf.rviz'
    )

    return LaunchDescription([
        # Declare launch arguments
        DeclareLaunchArgument('model', default_value=model_path, description='Model to load'),
        DeclareLaunchArgument('gui', default_value='True', description='Launch with GUI'),

        # Set the robot description parameter
        Node(
            package='xacro',
            executable='xacro',
            name='xacro',
            output='screen',
            parameters=[{
                'robot_description': Command([
                    'xacro ',
                    LaunchConfiguration('model'),
                    ' use_nominal_extrinsics:=true add_plug:=true'
                ])
            }]
        ),

        # Publish the robot state
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'publish_frequency': 30.0}],
            output='screen'
        ),

        # Include the Gazebo launch file
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gazebo_launch_path),
            launch_arguments={'model': LaunchConfiguration('model')}.items()
        ),

        # Launch RViz
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config_path],
            output='screen',
            condition=IfCondition(LaunchConfiguration('gui'))
        ),
    ])
