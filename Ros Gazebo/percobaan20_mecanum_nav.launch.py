"""
PERCOBAAN 20 – Robot Mecanum Navigasi Otonom
=============================================
Tujuan:
  - Navigasi otonom menggunakan robot mecanum
  - Memanfaatkan kemampuan gerak lateral mecanum wheel

Prasyarat: Jalankan percobaan19 dulu untuk membuat peta.

Cara menjalankan:
  ros2 launch gazebo_praktikum percobaan20_mecanum_nav.launch.py \\
    map:=/path/to/map_mecanum.yaml

Di RViz2:
  1. "2D Pose Estimate" → posisi awal robot
  2. "2D Nav Goal" → target tujuan
"""

import os
import xacro
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess,
                             IncludeLaunchDescription, RegisterEventHandler,
                             TimerAction)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share    = FindPackageShare('gazebo_praktikum').find('gazebo_praktikum')
    gazebo_share = FindPackageShare('gazebo_ros').find('gazebo_ros')

    xacro_file  = os.path.join(pkg_share, 'urdf',   'robot_mecanum.urdf.xacro')
    world_file  = os.path.join(pkg_share, 'worlds', 'percobaan7_navigasi_world.world')
    nav2_params = os.path.join(pkg_share, 'config', 'nav2_params.yaml')
    rviz_file   = os.path.join(pkg_share, 'rviz',   'percobaan7_navigasi.rviz')
    default_map = os.path.join(pkg_share, 'maps',   'my_map.yaml')

    arg_gui = DeclareLaunchArgument('gui', default_value='true')
    arg_map = DeclareLaunchArgument('map', default_value=default_map)

    _desc_xml = xacro.process_file(xacro_file).toxml()
    _sym = os.path.expanduser(
        '~/ros_praktikum/install/gazebo_praktikum/share/gazebo_praktikum')
    if os.path.isdir(_sym):
        _desc_xml = _desc_xml.replace('package://gazebo_praktikum/', f'file://{_sym}/')
    robot_description = ParameterValue(_desc_xml, value_type=str)

    kill_stale = ExecuteProcess(
        cmd=['bash', '-c',
             'pkill -9 -x gzserver 2>/dev/null; pkill -9 -x gzclient 2>/dev/null; true'],
        output='screen',
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_share, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'world': world_file,
            'gui':   LaunchConfiguration('gui'),
        }.items(),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'publish_frequency': 50.0,
        }],
    )

    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
    )

    spawn_entity = TimerAction(
        period=2.0,
        actions=[Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=[
                '-entity', 'robot_mecanum',
                '-topic',  '/robot_description',
                '-x', '-5.0', '-y', '-5.0', '-z', '0.05',
            ],
            output='screen',
        )]
    )

    nav2 = TimerAction(
        period=5.0,
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                FindPackageShare('nav2_bringup').find('nav2_bringup'),
                '/launch/bringup_launch.py',
            ]),
            launch_arguments={
                'map':          LaunchConfiguration('map'),
                'use_sim_time': 'true',
                'params_file':  nav2_params,
            }.items(),
        )]
    )

    rviz2 = TimerAction(
        period=6.0,
        actions=[Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_file],
            output='screen',
        )]
    )

    return LaunchDescription([
        arg_gui, arg_map,
        kill_stale,
        RegisterEventHandler(OnProcessExit(target_action=kill_stale, on_exit=[gazebo])),
        robot_state_publisher,
        joint_state_publisher,
        spawn_entity,
        nav2,
        rviz2,
    ])
