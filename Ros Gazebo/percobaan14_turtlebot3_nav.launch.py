"""
PERCOBAAN 14 – TurtleBot3 Navigasi Otonom
============================================
Tujuan:
  - Navigasi otonom menggunakan Nav2 dengan TurtleBot3
  - Menggunakan peta hasil SLAM
  - Memberi tujuan navigasi melalui RViz2

Prasyarat:
  Jalankan percobaan13 dulu untuk membuat peta.

Cara menjalankan:
  ros2 launch gazebo_praktikum percobaan14_turtlebot3_nav.launch.py \\
    map:=/path/to/map_turtlebot3.yaml

Di RViz2:
  1. Klik "2D Pose Estimate" → klik posisi awal robot
  2. Klik "2D Nav Goal" → klik target tujuan
"""

import os
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess,
                             IncludeLaunchDescription, RegisterEventHandler,
                             SetEnvironmentVariable, TimerAction)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share   = FindPackageShare('gazebo_praktikum').find('gazebo_praktikum')
    nav2_params = os.path.join(pkg_share, 'config', 'nav2_params.yaml')
    rviz_file   = os.path.join(pkg_share, 'rviz', 'percobaan7_navigasi.rviz')
    default_map = os.path.join(pkg_share, 'maps', 'my_map.yaml')

    set_model = SetEnvironmentVariable('TURTLEBOT3_MODEL', 'waffle')
    arg_gui = DeclareLaunchArgument('gui', default_value='true')
    arg_map = DeclareLaunchArgument('map', default_value=default_map,
                                    description='Path ke file peta .yaml')

    kill_stale = ExecuteProcess(
        cmd=['bash', '-c',
             'pkill -9 -x gzserver 2>/dev/null; pkill -9 -x gzclient 2>/dev/null; true'],
        output='screen',
    )

    turtlebot3_launch = TimerAction(
        period=1.0,
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                FindPackageShare('turtlebot3_gazebo').find('turtlebot3_gazebo'),
                '/launch/turtlebot3_world.launch.py',
            ]),
        )]
    )

    nav2 = TimerAction(
        period=8.0,
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
        period=8.0,
        actions=[Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_file],
            output='screen',
        )]
    )

    return LaunchDescription([
        set_model,
        arg_gui, arg_map,
        kill_stale,
        RegisterEventHandler(OnProcessExit(target_action=kill_stale, on_exit=[turtlebot3_launch])),
        nav2,
        rviz2,
    ])
