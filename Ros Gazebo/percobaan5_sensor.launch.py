"""
PERCOBAAN 5 – Sensor Robot: Kamera & LIDAR
============================================
Tujuan:
  - Menambahkan plugin sensor kamera dan LIDAR pada XACRO robot
  - Membaca data sensor melalui topik ROS 2
  - Visualisasi image kamera dan laser scan di RViz2

Cara menjalankan:
  ros2 launch gazebo_praktikum percobaan5_sensor.launch.py

Topik sensor:
  /robot/camera/image_raw       - gambar kamera (sensor_msgs/Image)
  /robot/camera/camera_info     - kalibrasi kamera
  /scan                         - laser scan 360° (sensor_msgs/LaserScan)
  /odom                         - odometri (nav_msgs/Odometry)

Teleop (terminal baru):
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

    xacro_file = os.path.join(pkg_share, 'urdf', 'robot_lengkap.urdf.xacro')
    world_file = os.path.join(pkg_share, 'worlds', 'percobaan5_sensor_world.world')
    rviz_file  = os.path.join(pkg_share, 'rviz',  'percobaan5_sensor.rviz')

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
                '-entity', 'robot_sensor',
                '-topic',  '/robot_description',
                '-x', '0.0', '-y', '0.0', '-z', '0.05',
            ],
            output='screen',
        )]
    )

    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_file],
        output='screen',
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
