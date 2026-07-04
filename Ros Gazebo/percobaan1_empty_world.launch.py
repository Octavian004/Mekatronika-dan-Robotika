"""
PERCOBAAN 1 – Menjalankan Gazebo dengan Empty World
====================================================
Tujuan:
  - Memahami cara membuka Gazebo dari ROS 2
  - Mengenal antarmuka Gazebo: toolbar, panel scene, physics panel
  - Memahami file .world (SDF format)

Cara menjalankan:
  ros2 launch gazebo_praktikum percobaan1_empty_world.launch.py

Argumen opsional:
  gui:=true/false   (default: true)
  verbose:=true     (tampilkan log Gazebo)
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

    world_file = os.path.join(pkg_share, 'worlds', 'percobaan1_empty_world.world')

    # ── Argumen ──────────────────────────────────────────────────────────────
    arg_gui     = DeclareLaunchArgument('gui',     default_value='true',
                                        description='Tampilkan GUI Gazebo')
    arg_verbose = DeclareLaunchArgument('verbose', default_value='false',
                                        description='Verbose output Gazebo')
    arg_paused  = DeclareLaunchArgument('paused',  default_value='false',
                                        description='Mulai simulasi dalam keadaan pause')

    # ── Bersihkan proses Gazebo lama ──────────────────────────────────────────
    kill_stale = ExecuteProcess(
        cmd=['bash', '-c',
             'pkill -9 -x gzserver 2>/dev/null; pkill -9 -x gzclient 2>/dev/null; true'],
        output='screen',
    )

    # ── Gazebo server + client ────────────────────────────────────────────────
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_share, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'world':   world_file,
            'gui':     LaunchConfiguration('gui'),
            'verbose': LaunchConfiguration('verbose'),
            'paused':  LaunchConfiguration('paused'),
        }.items(),
    )

    return LaunchDescription([
        arg_gui,
        arg_verbose,
        arg_paused,
        kill_stale,
        RegisterEventHandler(OnProcessExit(target_action=kill_stale, on_exit=[gazebo])),
    ])
