"""
PERCOBAAN 8 – Multi Robot: Dua Robot di Satu World
====================================================
Tujuan:
  - Mengelola multiple robot di Gazebo menggunakan namespace
  - Memastikan topik tidak bentrok antar robot
  - Mengendalikan dua robot secara independen

Cara menjalankan:
  ros2 launch gazebo_praktikum percobaan8_multi_robot.launch.py

Topik Robot 1 (namespace /robot1):
  /robot1/cmd_vel   /robot1/odom   /robot1/scan

Topik Robot 2 (namespace /robot2):
  /robot2/cmd_vel   /robot2/odom   /robot2/scan

Teleop Robot 1 (terminal baru):
  ros2 run teleop_twist_keyboard teleop_twist_keyboard \\
    --ros-args --remap /cmd_vel:=/robot1/cmd_vel

Teleop Robot 2 (terminal baru):
  ros2 run teleop_twist_keyboard teleop_twist_keyboard \\
    --ros-args --remap /cmd_vel:=/robot2/cmd_vel
"""

import os
import xacro
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess, GroupAction,
                             IncludeLaunchDescription, RegisterEventHandler,
                             TimerAction)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share    = FindPackageShare('gazebo_praktikum').find('gazebo_praktikum')
    gazebo_share = FindPackageShare('gazebo_ros').find('gazebo_ros')

    xacro_file = os.path.join(pkg_share, 'urdf',   'robot_lengkap.urdf.xacro')
    world_file = os.path.join(pkg_share, 'worlds', 'percobaan9_multi_robot.world')
    rviz_file  = os.path.join(pkg_share, 'rviz',   'percobaan8_multi_robot.rviz')

    arg_gui = DeclareLaunchArgument('gui', default_value='true')

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

    def robot_group(ns, x, y, yaw, delay):
        robot_desc = ParameterValue(
            xacro.process_file(xacro_file).toxml(),
            value_type=str
        )
        return GroupAction(actions=[
            PushRosNamespace(ns),
            Node(
                package='robot_state_publisher',
                executable='robot_state_publisher',
                output='screen',
                parameters=[{
                    'robot_description': robot_desc,
                    'publish_frequency': 50.0,
                    'frame_prefix': ns + '/',
                }],
            ),
            Node(
                package='joint_state_publisher',
                executable='joint_state_publisher',
            ),
            TimerAction(
                period=delay,
                actions=[Node(
                    package='gazebo_ros',
                    executable='spawn_entity.py',
                    name=f'spawn_{ns}',
                    arguments=[
                        '-entity', ns,
                        '-topic',  f'/{ns}/robot_description',
                        '-x', str(x), '-y', str(y), '-z', '0.05',
                        '-Y', str(yaw),
                    ],
                    output='screen',
                )]
            ),
        ])

    robot1_group = robot_group('robot1', x=-3.0, y=0.0,  yaw=0.0,     delay=2.0)
    robot2_group = robot_group('robot2', x= 3.0, y=0.0,  yaw=3.14159, delay=2.5)

    rviz2 = TimerAction(
        period=5.0,
        actions=[Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_file],
            output='screen',
        )]
    )

    return LaunchDescription([
        arg_gui,
        kill_stale,
        RegisterEventHandler(OnProcessExit(target_action=kill_stale, on_exit=[gazebo])),
        robot1_group,
        robot2_group,
        rviz2,
    ])
