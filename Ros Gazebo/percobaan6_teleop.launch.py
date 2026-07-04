"""
PERCOBAAN 6 – Teleoperasi Robot dengan Keyboard
=================================================
Tujuan:
  - Mengendalikan robot dengan keyboard melalui topik /cmd_vel
  - Memahami Gazebo diff_drive plugin (libgazebo_ros_diff_drive)
  - Memantau odometri dan kecepatan robot

Cara menjalankan:
  ros2 launch gazebo_praktikum percobaan6_teleop.launch.py

Teleop (terminal baru, setelah Gazebo terbuka):
  ros2 run teleop_twist_keyboard teleop_twist_keyboard

Tombol teleop:
  i / ,   maju / mundur
  j / l   belok kiri / kanan
  k       berhenti

Pantau odometri:
  ros2 topic echo /odom

Topik aktif:
  /cmd_vel        - perintah kecepatan (dikirim teleop)
  /odom           - odometri dari Gazebo diff drive plugin
  /scan           - LIDAR data
  /camera/image_raw - kamera
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

    xacro_file = os.path.join(pkg_share, 'urdf',   'robot_lengkap.urdf.xacro')
    world_file = os.path.join(pkg_share, 'worlds', 'percobaan4_robot_world.world')
    rviz_file  = os.path.join(pkg_share, 'rviz',   'percobaan6_teleop.rviz')

    arg_gui = DeclareLaunchArgument('gui', default_value='true')

    robot_description = ParameterValue(
        xacro.process_file(xacro_file).toxml(),
        value_type=str
    )

    # ── Bersihkan proses Gazebo lama ──────────────────────────────────────────
    kill_stale = ExecuteProcess(
        cmd=['bash', '-c',
             'pkill -9 -x gzserver 2>/dev/null; pkill -9 -x gzclient 2>/dev/null; true'],
        output='screen',
    )

    # ── Gazebo (mulai setelah kill selesai) ───────────────────────────────────
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_share, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'world': world_file,
            'gui':   LaunchConfiguration('gui'),
        }.items(),
    )
    gazebo_after_kill = RegisterEventHandler(
        OnProcessExit(target_action=kill_stale, on_exit=[gazebo])
    )

    # ── Robot State Publisher ─────────────────────────────────────────────────
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'publish_frequency': 50.0,
        }],
    )

    # ── Joint State Publisher (visualisasi roda di RViz2) ────────────────────
    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
    )

    # ── Spawn robot ───────────────────────────────────────────────────────────
    spawn_entity = TimerAction(
        period=2.0,
        actions=[Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            name='spawn_robot',
            arguments=[
                '-entity', 'robot_teleop',
                '-topic',  '/robot_description',
                '-x', '0.0', '-y', '0.0', '-z', '0.05',
            ],
            output='screen',
        )]
    )

    # ── RViz2 ─────────────────────────────────────────────────────────────────
    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_file],
        output='screen',
    )

    return LaunchDescription([
        arg_gui,
        kill_stale,
        gazebo_after_kill,
        robot_state_publisher,
        joint_state_publisher,
        spawn_entity,
        rviz2,
    ])
