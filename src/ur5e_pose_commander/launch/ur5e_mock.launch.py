"""Stage 1: UR5e with mock (fake) hardware + MoveIt + RViz, using the official UR packages.

Starts
  - ur_robot_driver (ur_control.launch.py) with use_mock_hardware:=true: ros2_control with a
    mock hardware interface that mirrors commands to states, so no robot or simulator is needed.
  - ur_moveit_config (ur_moveit.launch.py): move_group + RViz with the MotionPlanning panel.

Then run the pose commander in a separate terminal (it reads goals from stdin):
  ros2 run ur5e_pose_commander pose_commander
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    ur_type = LaunchConfiguration("ur_type")
    launch_rviz = LaunchConfiguration("launch_rviz")

    driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("ur_robot_driver"), "launch", "ur_control.launch.py"])),
        launch_arguments={
            "ur_type": ur_type,
            "robot_ip": "0.0.0.0",  # unused with mock hardware, but required by the launch file
            "use_mock_hardware": "true",
            "launch_rviz": "false",  # RViz comes from MoveIt below
        }.items(),
    )

    moveit = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("ur_moveit_config"), "launch", "ur_moveit.launch.py"])),
        launch_arguments={"ur_type": ur_type, "launch_rviz": launch_rviz}.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument("ur_type", default_value="ur5e", description="UR robot model"),
        DeclareLaunchArgument("launch_rviz", default_value="true", description="Start RViz"),
        driver,
        moveit,
    ])
