"""
PERCOBAAN 4 – Spawn Robot URDF ke Gazebo
==========================================
Tujuan:
  - Mempelajari cara memasukkan (spawn) robot ke simulasi Gazebo
  - Mengenal service /spawn_entity dari gazebo_ros
  - Melihat robot di Gazebo dan TF tree di RViz2

Cara menjalankan:
  ros2 launch gazebo_praktikum percobaan4_spawn_robot.launch.py

Argumen:
  x:=0.0  y:=0.0  yaw:=0.0   (posisi awal robot)

Topik aktif:
  /odom           - odometri diferensial
  /joint_states   - status joint roda
"""

import os
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess,
                             IncludeLaunchDescription, RegisterEventHandler,
                             TimerAction)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (LaunchConfiguration,
                                   PathJoinSubstitution)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share    = FindPackageShare('gazebo_praktikum').find('gazebo_praktikum')
    gazebo_share = FindPackageShare('gazebo_ros').find('gazebo_ros')

    urdf_file  = os.path.join(pkg_share, 'urdf', 'robot_sederhana.urdf')
    world_file = os.path.join(pkg_share, 'worlds', 'percobaan4_robot_world.world')
    rviz_file  = os.path.join(pkg_share, 'rviz', 'percobaan4_spawn.rviz')

    # ── Argumen ───────────────────────────────────────────────────────────────
    arg_gui = DeclareLaunchArgument('gui',    default_value='true')
    arg_x   = DeclareLaunchArgument('x',     default_value='0.0')
    arg_y   = DeclareLaunchArgument('y',     default_value='0.0')
    arg_yaw = DeclareLaunchArgument('yaw',   default_value='0.0')

    # robot_description dari URDF (baca langsung agar aman di path dengan spasi)
    with open(urdf_file, 'r') as f:
        urdf_content = f.read()

    robot_description = ParameterValue(urdf_content, value_type=str)
    # ── Bersihkan proses Gazebo lama ─────────────────────────────────────────
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
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'publish_frequency': 50.0,
        }],
    )

    # ── Spawn entity (delay 2s agar Gazebo siap) ──────────────────────────────
    spawn_entity = TimerAction(
        period=2.0,
        actions=[Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            name='spawn_robot',
            output='screen',
            arguments=[
                '-entity',          'robot_sederhana',
                '-topic',           '/robot_description',
                '-x',               LaunchConfiguration('x'),
                '-y',               LaunchConfiguration('y'),
                '-z',               '0.05',
                '-Y',               LaunchConfiguration('yaw'),
            ],
        )]
    )

    # ── Joint State Publisher ─────────────────────────────────────────────────
    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
    )

    # ── RViz2 ─────────────────────────────────────────────────────────────────
    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_file],
    )

    return LaunchDescription([
        arg_gui, arg_x, arg_y, arg_yaw,
        kill_stale,
        RegisterEventHandler(OnProcessExit(target_action=kill_stale, on_exit=[gazebo])),
        robot_state_publisher,
        joint_state_publisher,
        spawn_entity,
        rviz2,
    ])
