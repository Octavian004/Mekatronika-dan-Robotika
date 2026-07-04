"""
PERCOBAAN 2 – Model & Shapes di Gazebo
========================================
Tujuan:
  - Belajar menambahkan objek 3D (box, cylinder, sphere) ke world
  - Memahami properti fisika: mass, inertia, friction, collision
  - Mengamati interaksi objek dengan gravitasi dan tumbukan

Cara menjalankan:
  ros2 launch gazebo_praktikum percobaan2_shapes.launch.py

Topik yang dapat dipantau:
  ros2 topic list
"""

import os
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess,
                             IncludeLaunchDescription, RegisterEventHandler)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share    = FindPackageShare('gazebo_praktikum').find('gazebo_praktikum')
    gazebo_share = FindPackageShare('gazebo_ros').find('gazebo_ros')

    world_file = os.path.join(pkg_share, 'worlds', 'percobaan2_shapes_world.world')

    arg_gui    = DeclareLaunchArgument('gui',   default_value='true')
    arg_paused = DeclareLaunchArgument('paused', default_value='false')

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
            'world':  world_file,
            'gui':    LaunchConfiguration('gui'),
            'paused': LaunchConfiguration('paused'),
        }.items(),
    )

    return LaunchDescription([
        arg_gui,
        arg_paused,
        kill_stale,
        RegisterEventHandler(OnProcessExit(target_action=kill_stale, on_exit=[gazebo])),
    ])
