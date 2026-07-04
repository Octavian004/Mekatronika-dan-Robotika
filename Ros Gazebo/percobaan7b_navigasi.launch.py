"""
PERCOBAAN 7B – Navigasi Otonom dengan Nav2
============================================
Tujuan:
  - Menggunakan peta hasil SLAM untuk navigasi otonom
  - Memahami stack Nav2: planner, controller, recovery
  - Memberi tujuan robot lewat RViz2 (2D Nav Goal)

Prasyarat:
  Jalankan percobaan7a_slam.launch.py dulu → simpan peta

Cara menjalankan:
  ros2 launch gazebo_praktikum percobaan7b_navigasi.launch.py \
    map:=<path>/maps/my_map.yaml

Argumen:
  map:=...   path absolut file peta .yaml (default: maps/my_map.yaml)

Di RViz2:
  1. Klik "2D Pose Estimate" → klik posisi awal robot di peta
  2. Klik "2D Nav Goal"      → klik target tujuan robot
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

    xacro_file  = os.path.join(pkg_share, 'urdf',   'robot_lengkap.urdf.xacro')
    world_file  = os.path.join(pkg_share, 'worlds', 'percobaan7_navigasi_world.world')
    nav2_params = os.path.join(pkg_share, 'config', 'nav2_params.yaml')
    rviz_file   = os.path.join(pkg_share, 'rviz',   'percobaan7_navigasi.rviz')
    default_map = os.path.join(pkg_share, 'maps',   'my_map.yaml')

    # ── Argumen ───────────────────────────────────────────────────────────────
    arg_gui = DeclareLaunchArgument('gui', default_value='true')
    arg_map = DeclareLaunchArgument('map', default_value=default_map,
                                    description='Path ke file peta .yaml hasil SLAM')

    robot_description = ParameterValue(
        xacro.process_file(xacro_file).toxml(),
        value_type=str
    )

    kill_stale = ExecuteProcess(
        cmd=['bash', '-c',
             'pkill -9 -x gzserver 2>/dev/null; pkill -9 -x gzclient 2>/dev/null; true'],
        output='screen',
    )

    # ── Gazebo ────────────────────────────────────────────────────────────────
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_share, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'world': world_file,
            'gui':   LaunchConfiguration('gui'),
        }.items(),
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
            arguments=[
                '-entity', 'robot_nav',
                '-topic',  '/robot_description',
                '-x', '-5.0', '-y', '-5.0', '-z', '0.05',
            ],
            output='screen',
        )]
    )

    # ── Nav2 bringup ─────────────────────────────────────────────────────────
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

    # ── RViz2 dengan konfigurasi Nav2 ─────────────────────────────────────────
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
