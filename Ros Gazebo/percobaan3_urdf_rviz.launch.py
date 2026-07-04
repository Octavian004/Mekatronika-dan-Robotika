"""
PERCOBAAN 3 – Membangun URDF & Visualisasi di RViz 2
======================================================
Tujuan:
  - Memahami format URDF: link, joint, collision, visual
  - Visualisasi model robot di RViz2 tanpa Gazebo
  - Menggunakan robot_state_publisher dan joint_state_publisher_gui

Cara menjalankan:
  ros2 launch gazebo_praktikum percobaan3_urdf_rviz.launch.py

Catatan:
  - Gerakkan slider joint di jendela Joint State Publisher GUI
  - Perhatikan model 3D robot bergerak di RViz2
  - Amati pohon TF di panel Displays
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = FindPackageShare('gazebo_praktikum').find('gazebo_praktikum')

    urdf_file  = os.path.join(pkg_share, 'urdf', 'robot_sederhana.urdf')
    rviz_file  = os.path.join(pkg_share, 'rviz', 'percobaan3_urdf.rviz')

    # robot_description dari URDF (baca langsung agar aman di path dengan spasi)
    with open(urdf_file, 'r') as f:
        urdf_content = f.read()

    robot_description = ParameterValue(urdf_content, value_type=str)

    # ── Nodes ─────────────────────────────────────────────────────────────────
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

    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',
    )

    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_file],
    )

    return LaunchDescription([
        robot_state_publisher,
        joint_state_publisher_gui,
        rviz2,
    ])
