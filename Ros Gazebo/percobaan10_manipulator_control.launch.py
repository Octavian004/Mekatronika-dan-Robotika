"""
PERCOBAAN 10 – Manipulator dengan ros2_control
=================================================
Tujuan:
  - Mengontrol robot manipulator menggunakan ros2_control framework
  - Memahami JointGroupPositionController
  - Demo gerakan otomatis manipulator

Cara menjalankan:
  ros2 launch gazebo_praktikum percobaan10_manipulator_control.launch.py

Kontrol manual (terminal baru):
  ros2 topic pub /arm_position_controller/commands \\
    std_msgs/msg/Float64MultiArray "data: [1.57, 0.5, -1.0]" --once

Demo otomatis: script demo_manipulator.py berjalan otomatis setelah launch.
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

    xacro_file = os.path.join(pkg_share, 'urdf',   'robot_manipulator.urdf.xacro')
    ctrl_file  = os.path.join(pkg_share, 'config', 'manipulator_controllers.yaml')
    rviz_file  = os.path.join(pkg_share, 'rviz',   'percobaan10_manipulator_control.rviz')

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
        launch_arguments={'gui': LaunchConfiguration('gui')}.items(),
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

    spawn_entity = TimerAction(
        period=2.0,
        actions=[Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            name='spawn_manipulator',
            arguments=[
                '-entity', 'robot_manipulator',
                '-topic',  '/robot_description',
                '-x', '0.0', '-y', '0.0', '-z', '0.0',
            ],
            output='screen',
        )]
    )

    # Controller Manager (no namespace, simple setup)
    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[
            {'robot_description': robot_description},
            ctrl_file,
        ],
        output='screen',
    )

    # Spawn controllers after controller_manager is ready
    joint_state_broadcaster = TimerAction(
        period=4.0,
        actions=[Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster'],
            output='screen',
        )]
    )

    arm_controller = TimerAction(
        period=5.0,
        actions=[Node(
            package='controller_manager',
            executable='spawner',
            arguments=['arm_position_controller'],
            output='screen',
        )]
    )

    # Demo script
    demo_script = TimerAction(
        period=7.0,
        actions=[Node(
            package='gazebo_praktikum',
            executable='demo_manipulator.py',
            name='demo_gerak_manipulator',
            output='screen',
        )]
    )

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
        spawn_entity,
        controller_manager,
        joint_state_broadcaster,
        arm_controller,
        demo_script,
        rviz2,
    ])
