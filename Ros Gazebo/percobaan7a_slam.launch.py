"""
PERCOBAAN 7A – SLAM: Membuat Peta dengan slam_toolbox
=======================================================
Tujuan:
  - Memahami konsep SLAM (Simultaneous Localization And Mapping)
  - Menggunakan slam_toolbox (pengganti gmapping di ROS2)
  - Membuat peta ruangan dari data LIDAR sambil robot bergerak

Cara menjalankan:
  ros2 launch gazebo_praktikum percobaan7a_slam.launch.py

Setelah peta selesai, simpan peta (terminal baru):
  ros2 run nav2_map_server map_saver_cli \
    -f ~/ros2_ws/src/gazebo_praktikum/maps/my_map

Lanjutkan ke navigasi:
  ros2 launch gazebo_praktikum percobaan7b_navigasi.launch.py

Teleop selama SLAM (terminal baru):
  ros2 run teleop_twist_keyboard teleop_twist_keyboard
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
    slam_params = os.path.join(pkg_share, 'config', 'slam_params.yaml')
    rviz_file   = os.path.join(pkg_share, 'rviz',   'percobaan7_slam.rviz')

    arg_gui = DeclareLaunchArgument('gui', default_value='true')

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

    # ── Spawn robot di pojok labirin ──────────────────────────────────────────
    spawn_entity = TimerAction(
        period=2.0,
        actions=[Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=[
                '-entity', 'robot_slam',
                '-topic',  '/robot_description',
                '-x', '-5.0', '-y', '-5.0', '-z', '0.05',
            ],
            output='screen',
        )]
    )

    # ── SLAM Toolbox (async mode) ─────────────────────────────────────────────
    slam_toolbox = TimerAction(
        period=4.0,
        actions=[Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[slam_params],
            remappings=[('/scan', '/scan')],
        )]
    )

    # ── Joint State Publisher ─────────────────────────────────────────────────
    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
    )

    # ── RViz2 ─────────────────────────────────────────────────────────────────
    rviz2 = TimerAction(
        period=4.0,
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
        slam_toolbox,
        rviz2,
    ])
