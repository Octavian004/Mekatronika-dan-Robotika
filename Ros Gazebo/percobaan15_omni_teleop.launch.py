"""
PERCOBAAN 15 – Robot Omni-Directional Teleop
===============================================
Tujuan:
  - Memahami konsep robot omnidirectional (4 roda omni)
  - Mengendalikan robot ke segala arah (maju, mundur, kiri, kanan, diagonal)
  - Memahami perbedaan dengan differential drive

Cara menjalankan:
  ros2 launch gazebo_praktikum percobaan15_omni_teleop.launch.py

Teleop (terminal baru):
  ros2 run teleop_twist_keyboard teleop_twist_keyboard

Catatan: Robot omni bisa bergerak ke samping (linear.y).
  Gunakan tombol 'u','o' untuk gerakan diagonal,
  'j','l' untuk rotasi, 'i',',' untuk maju/mundur.
  
  Untuk gerakan lateral murni (geser kiri/kanan), publish manual:
    ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \\
      "{linear: {y: 0.3}}" --once
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

    xacro_file = os.path.join(pkg_share, 'urdf',   'robot_omni.urdf.xacro')
    world_file = os.path.join(pkg_share, 'worlds', 'percobaan5_sensor_world.world')
    rviz_file  = os.path.join(pkg_share, 'rviz',   'percobaan15_omni.rviz')

    arg_gui = DeclareLaunchArgument('gui', default_value='true')

    # Fix: replace package:// URIs with file:// symlink path to avoid
    # resource_retriever curl failure on paths containing spaces.
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
                '-entity', 'robot_omni',
                '-topic',  '/robot_description',
                '-x', '0.0', '-y', '0.0', '-z', '0.05',
            ],
            output='screen',
        )]
    )

    rviz2 = TimerAction(
        period=3.0,
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
        robot_state_publisher,
        joint_state_publisher,
        spawn_entity,
        rviz2,
    ])
