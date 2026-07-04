"""
PERCOBAAN 9 - Robot Manipulator 3-DOF (Visualisasi RViz2)
===========================================================
Tujuan:
  - Memahami URDF robot lengan (manipulator)
  - Mengontrol joint menggunakan joint_state_publisher_gui
  - Visualisasi gerakan manipulator di RViz2

Cara menjalankan:
  ros2 launch gazebo_praktikum percobaan9_manipulator.launch.py

Kontrol joint:
  Gunakan slider di joint_state_publisher_gui untuk menggerakkan joint.
  Pergerakan joint langsung terlihat di RViz2 tanpa perlu Gazebo.
"""

import os
import xacro
from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = FindPackageShare("gazebo_praktikum").find("gazebo_praktikum")

    xacro_file = os.path.join(pkg_share, "urdf", "robot_manipulator.urdf.xacro")
    rviz_file  = os.path.join(pkg_share, "rviz", "percobaan9_manipulator.rviz")

    robot_description = ParameterValue(
        xacro.process_file(xacro_file).toxml(),
        value_type=str
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[{
            "robot_description": robot_description,
            "publish_frequency": 50.0,
        }],
    )

    # GUI slider untuk kontrol joint - langsung tampil di RViz2
    joint_state_publisher_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        output="screen",
    )

    rviz2 = TimerAction(
        period=1.0,
        actions=[Node(
            package="rviz2",
            executable="rviz2",
            arguments=["-d", rviz_file],
            output="screen",
        )]
    )

    return LaunchDescription([
        robot_state_publisher,
        joint_state_publisher_gui,
        rviz2,
    ])
