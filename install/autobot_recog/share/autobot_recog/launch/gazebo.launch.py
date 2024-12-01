from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration, FindPackageShare, Command
from launch_ros.actions import Node
import os

def generate_launch_description():
    # Define the arguments for the launch file
    return LaunchDescription([
        DeclareLaunchArgument('paused', default_value='false', description='Pause the simulation'),
        DeclareLaunchArgument('use_sim_time', default_value='true', description='Use simulation time'),
        DeclareLaunchArgument('gui', default_value='true', description='Launch with GUI'),
        DeclareLaunchArgument('headless', default_value='false', description='Launch in headless mode'),
        DeclareLaunchArgument('debug', default_value='false', description='Enable debug mode'),
        DeclareLaunchArgument('model', default_value=os.path.join(
            get_package_share_directory('realsense2_description'),
            'urdf/test_d435_camera.urdf.xacro'), description='Model to load'),

        # Load the robot description parameter
        Node(
            package='ros2_control',
            executable='controller_manager',
            parameters=[{
                'robot_description': Command(['xacro ', LaunchConfiguration('model')])
            }],
            output='screen'
        ),

        # Include the empty world launch file
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory('gazebo_ros'),
                    'launch',
                    'empty_world.launch.py')
            ),
            launch_arguments={
                'debug': LaunchConfiguration('debug'),
                'gui': LaunchConfiguration('gui'),
                'paused': LaunchConfiguration('paused'),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'headless': LaunchConfiguration('headless'),
            }.items()
        ),

        # Spawn the robot model in Gazebo
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=[
                '-z', '1.0',
                '-entity', 'robot',
                '-file', LaunchConfiguration('model')
            ],
            output='screen'
        ),
    ])
