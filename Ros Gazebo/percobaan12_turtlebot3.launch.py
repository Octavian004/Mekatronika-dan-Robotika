"""
PERCOBAAN 12 – TurtleBot3 di Gazebo
======================================
Tujuan:
  - Mengenal robot TurtleBot3 (platform robot populer untuk riset)
  - Spawn TurtleBot3 Waffle di Gazebo world
  - Memahami topik standar TurtleBot3

Cara menjalankan:
  ros2 launch gazebo_praktikum percobaan12_turtlebot3.launch.py

Teleop (terminal baru):
  ros2 run teleop_twist_keyboard teleop_twist_keyboard

Topik penting:
  /cmd_vel         - perintah kecepatan
  /odom            - odometri
  /scan            - LIDAR 360°
  /camera/image_raw - kamera (Waffle only)
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
    pkg_share = FindPackageShare('gazebo_praktikum').find('gazebo_praktikum')
    rviz_file = os.path.join(pkg_share, 'rviz', 'percobaan12_turtlebot3.rviz')

    # Set model TurtleBot3
    set_model = SetEnvironmentVariable('TURTLEBOT3_MODEL', 'waffle')

    arg_gui = DeclareLaunchArgument('gui', default_value='true')

    kill_stale = ExecuteProcess(
        cmd=['bash', '-c',
             'pkill -9 -x gzserver 2>/dev/null; pkill -9 -x gzclient 2>/dev/null; true'],
        output='screen',
    )

    # Launch TurtleBot3 Gazebo world
    turtlebot3_launch = TimerAction(
        period=1.0,
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                FindPackageShare('turtlebot3_gazebo').find('turtlebot3_gazebo'),
                '/launch/turtlebot3_world.launch.py',
            ]),
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
        set_model,
        arg_gui,
        kill_stale,
        RegisterEventHandler(OnProcessExit(target_action=kill_stale, on_exit=[turtlebot3_launch])),
        rviz2,
    ])
