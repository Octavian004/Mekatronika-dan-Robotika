"""
PERCOBAAN 13 – TurtleBot3 SLAM
=================================
Tujuan:
  - Membuat peta menggunakan SLAM dengan TurtleBot3
  - Memahami proses mapping dengan robot nyata (simulasi)
  - Menyimpan peta hasil SLAM

Cara menjalankan:
  ros2 launch gazebo_praktikum percobaan13_turtlebot3_slam.launch.py

Teleop (terminal baru):
  ros2 run teleop_twist_keyboard teleop_twist_keyboard

Simpan peta (terminal baru, setelah peta selesai):
  ros2 run nav2_map_server map_saver_cli -f ~/map_turtlebot3
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
    pkg_share  = FindPackageShare('gazebo_praktikum').find('gazebo_praktikum')
    slam_params = os.path.join(pkg_share, 'config', 'slam_params.yaml')
    rviz_file  = os.path.join(pkg_share, 'rviz', 'percobaan7_slam.rviz')

    set_model = SetEnvironmentVariable('TURTLEBOT3_MODEL', 'waffle')
    arg_gui = DeclareLaunchArgument('gui', default_value='true')

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

    slam_toolbox = TimerAction(
        period=6.0,
        actions=[Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[slam_params],
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
        slam_toolbox,
        rviz2,
    ])
