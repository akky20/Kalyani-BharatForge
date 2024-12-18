#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():

    pkg_share = get_package_share_directory('autobot_recog')
    

    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')


    world_path = 'src/autobot_recog/worlds/warehouse_large.world'
    urdf_path = 'src/autobot_recog/urdf/velodyne_bot.sdf'


    declare_world_cmd = DeclareLaunchArgument(
        'world',
        default_value=world_path,
        description='Full path to the world model file to load'
    )

    declare_num_robots_cmd = DeclareLaunchArgument(
        'num_robots', 
        default_value='5',
        description='Number of robots to spawn'
    )


    world = LaunchConfiguration('world')
    num_robots = LaunchConfiguration('num_robots')


    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={'world': world}.items()
    )


    gzclient_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')
        )
    )


    ld = LaunchDescription()


    ld.add_action(declare_world_cmd)
    ld.add_action(declare_num_robots_cmd)

    ld.add_action(gzserver_cmd)
    ld.add_action(gzclient_cmd)

    robot_positions = [
        {'name': 'robot_0', 'x': 1.0, 'y': 5.0, 'z': 0.01},
        {'name': 'robot_1', 'x': 3.0, 'y': 1.0, 'z': 0.01},
        {'name': 'robot_2', 'x': 5.0, 'y': 7.0, 'z': 0.01},
        {'name': 'robot_3', 'x': 9, 'y': 4.0, 'z': 0.01},
        {'name': 'robot_4', 'x': 9.0, 'y': 7.0, 'z': 0.01},
    ]

    yolo_model_path = '/path/to/your/yolo/model'  

    for robot in robot_positions:
        robot_name = robot['name']
        robot_namespace = f'/{robot_name}'

        spawn_robot_cmd = Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=[
                '-entity', robot_name,
                '-file', urdf_path,
                '-x', str(robot['x']),
                '-y', str(robot['y']),
                '-z', str(robot['z']),
                '-robot_namespace', robot_namespace
            ],
            output='screen',
            parameters=[
                {'use_sim_time': True}
            ]
        )
        
        ld.add_action(spawn_robot_cmd)

        master_slave_node = Node(
            package='autobot_recog',  
            executable='master_slave_node',
            namespace=robot_name,
            name='master_slave_node',
            parameters=[{
                'agent_id': robot_name,
                'namespace': robot_name,
                'model_path': yolo_model_path
            }],
            output='screen'
        )
        ld.add_action(master_slave_node)

    # Chatbot Node 
    chatbot_node = Node(
        package='autobot_recog', 
        executable='chatbot_node',
        name='chatbot_node',
        output='screen'
    )
    ld.add_action(chatbot_node)

    # Dynamic Object Clearance Node (single instance)
    dynamic_object_clearance_node = Node(
        package='autobot_recog',  
        executable='dynamic_object_clearance_node',
        name='dynamic_object_clearance_node',
        output='screen',
        parameters=[
            {'expiration_time_seconds': 300}  
        ]
    )
    ld.add_action(dynamic_object_clearance_node)

    # Optional: Launch RViz for visualization
    rviz_config_path = os.path.join(pkg_share, 'rviz', 'multi_robot_view.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        output='screen'
    )
    ld.add_action(rviz_node)

    return ld