# UR5e End-Effector Pose Control

### ROS 2 Jazzy + MoveIt 2

## 1. Install and Build

```bash
sudo apt update
sudo apt install -y ros-jazzy-ur ros-jazzy-moveit

cd ~/ros2_Test
source /opt/ros/jazzy/setup.bash

rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
```

In every new terminal:

```bash
source ~/ros2_Test/install/setup.bash
```

---

# Stage 1: UR5e Simulation in RViz

## Terminal 1

Start the UR5e with fake hardware, MoveIt, and RViz:

```bash
source ~/ros2_Test/install/setup.bash

ros2 launch ur5e_pose_commander ur5e_mock.launch.py
```

Wait until you see:

```text
You can start planning now!
```

## Terminal 2

Start the pose commander:

```bash
source ~/ros2_Test/install/setup.bash

ros2 run ur5e_pose_commander pose_commander
```

Enter a goal:

```text
goal> 0.4 0.2 0.4 180 0 0
```

Example output:

```text
Goal: position [0.400, 0.200, 0.400] m
     rpy [180.0, 0.0, 0.0] deg

Goal accepted, planning and executing...
Goal reached.
```

### Input Format

| Input                  | Meaning                                     |
| ---------------------- | ------------------------------------------- |
| `x y z`                | Position in metres                          |
| `x y z roll pitch yaw` | Position in metres + orientation in degrees |
| `x y z qx qy qz qw`    | Position in metres + quaternion             |
| `current`              | Show current pose                           |
| `help`                 | Show input format                           |
| `q`                    | Quit                                        |

Example:

```text
0.4 0.2 0.4 180 0 0
```

---

# Stage 2: Isaac Sim

The ROS 2 control flow is:

```text
MoveIt
   ↓
arm_controller
   ↓
/isaac_joint_commands
   ↓
Isaac Sim
   ↓
/isaac_joint_states
   ↓
MoveIt
```

## Step 1: Start Isaac Sim

Open the UR5/UR5e scene in Isaac Sim and press **Play**.

Make sure these topics are active:

```text
/isaac_joint_commands
/isaac_joint_states
```

Check joint states:

```bash
ros2 topic hz /isaac_joint_states
```

You should see messages being published.

## Step 2: Start MoveIt

In Terminal 1:

```bash
source ~/ros2_Test/install/setup.bash

ros2 launch ur5_moveit_config demo.launch.py
```

Wait until you see:

```text
You can start planning now!
```

## Step 3: Start Pose Commander

In Terminal 2:

```bash
source ~/ros2_Test/install/setup.bash

ros2 run ur5e_pose_commander pose_commander
```

Enter a pose goal:

```text
goal> 0.4 0.2 0.4 180 0 0
```

MoveIt will plan the motion and send the joint commands to Isaac Sim.

---

## Important

The `ur5_moveit_config` package currently uses a **UR5 model**, not a UR5e model.

For an exact UR5e simulation, use the UR5e model and generate the MoveIt configuration from the UR5e URDF.

## Real UR5e

For a real UR5e, the setup is different:

```text
ROS 2 + MoveIt
      ↓
UR ROS 2 Driver
      ↓
Network
      ↓
Real UR5e
```

The package:

```bash
ros-jazzy-ur
```

is required for the ROS 2 driver when connecting to the real Universal Robot.
