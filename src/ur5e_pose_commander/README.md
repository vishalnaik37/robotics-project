# ur5e_pose_commander

Type a goal **position and orientation** for the UR5e end effector into the terminal. The robot plans and moves there using
the official [Universal Robots ROS 2 driver](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver) and MoveIt 2
(ROS 2 Jazzy).

```
 you (terminal)                                                  ros2_control
      │  x y z roll pitch yaw                                  ┌───────────────────────────┐
      ▼                                                         │ scaled_joint_trajectory_  │
 pose_commander ──/move_action──► move_group ──FollowJoint──►   │ controller                │──► mock hardware (Stage 1)
 (this package)   MoveGroup.action  (plan +    Trajectory       │                           │──► Isaac Sim     (Stage 2)
      ▲                              execute)                   │ joint_state_broadcaster   │──► real UR5e     (robot_ip)
      └──────────── TF (base_link → tool0): pose actually reached ◄────────────────────────┘
```

## 1. Install

```bash
sudo apt update
sudo apt install -y ros-jazzy-ur          # ur_robot_driver, ur_moveit_config, ur_description, ...

cd ~/ros2_Test
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select ur5e_pose_commander
```

## 2. Stage 1: UR5e with fake hardware in RViz

**Terminal 1: driver (mock hardware), MoveIt and RViz**

```bash
source ~/ros2_Test/install/setup.bash
ros2 launch ur5e_pose_commander ur5e_mock.launch.py
```

Wait for `You can start planning now!`. RViz opens with the UR5e.

This is the same as starting the two official launch files by hand:

```bash
ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur5e robot_ip:=0.0.0.0 use_mock_hardware:=true launch_rviz:=false
ros2 launch ur_moveit_config ur_moveit.launch.py ur_type:=ur5e launch_rviz:=true
```

**Terminal 2: the pose commander**

```bash
source ~/ros2_Test/install/setup.bash
ros2 run ur5e_pose_commander pose_commander
```

Then type goals at the prompt:

```
UR5e pose commander | group 'ur_manipulator', end effector 'tool0', frame 'base_link'
Current: position [...] m | rpy [...] deg | quat [...]

goal> 0.4 0.2 0.4 180 0 0
Goal   : position [0.400, 0.200, 0.400] m | rpy [180.0, 0.0, 0.0] deg | quat [1.000, 0.000, 0.000, 0.000]
Goal accepted, planning and executing...
Goal reached.
Reached: position [0.400, 0.201, 0.401] m | rpy [179.5, 0.1, -0.4] deg | quat [1.000, -0.003, -0.001, 0.004]

goal> 0.3 -0.3 0.5 90 0 0
...
goal> q
```

### Input format

| Input | Meaning |
|---|---|
| `x y z` | Position in **metres**, keep the current orientation |
| `x y z roll pitch yaw` | Position in metres, orientation in **degrees** (fixed-axis roll/pitch/yaw about X, Y, Z) |
| `x y z qx qy qz qw` | Position in metres, orientation as a quaternion (normalised automatically) |
| `current` | Print the current end-effector pose |
| `help` | Show the format |
| `q` | Quit |

The goal is the pose of `tool0` (the tool flange) in `base_link`. `0.4 0.2 0.4 180 0 0` puts the flange 40 cm in front,
20 cm to the side and 40 cm up, with the tool pointing straight down.

### Options

```bash
ros2 run ur5e_pose_commander pose_commander --goal 0.4 0.2 0.4 180 0 0   # one goal, no prompt
ros2 run ur5e_pose_commander pose_commander --velocity 0.5 --acceleration 0.5
ros2 run ur5e_pose_commander pose_commander --plan-only                  # plan, don't move
```

| Option | Default | Description |
|---|---|---|
| `--goal V...` | – | Goal as 3, 6 or 7 numbers. Runs once without the prompt |
| `--group` | auto | MoveIt planning group. By default it's read from move_group: `ur_manipulator` (UR5e config) or `arm` (Isaac Sim config) |
| `--ee-link` | `tool0` | Link placed at the goal |
| `--frame` | `base_link` | Frame the goal is expressed in |
| `--velocity` / `--acceleration` | `0.2` | Scaling of the joint velocity/acceleration limits (0–1) |
| `--planning-time` | `5.0` | Seconds allowed for planning |
| `--pos-tol` | `0.001` | Position tolerance radius [m] |
| `--rot-tol` | `0.01` | Orientation tolerance per axis [rad] (~0.57°) |
| `--plan-only` | off | Only plan, do not execute |

## 3. How it works

1. **Input.** The prompt line is parsed into a position and a quaternion (RPY in degrees is converted to a quaternion;
   with only `x y z`, the current orientation is read from TF and kept).
   Bad input is rejected. Goals farther than about 0.85 m (the UR5e reach) trigger a warning.
2. **Goal.** The script builds a `moveit_msgs/action/MoveGroup` goal with two constraints on `tool0`:
   - a *position constraint*: a sphere of radius `--pos-tol` around the target point
   - an *orientation constraint*: the target quaternion with a tolerance of `--rot-tol` on each axis

   `start_state.is_diff = true` tells MoveIt to start from the robot's current state.
3. **Planning (move_group).** MoveIt samples joint configurations that satisfy the goal (inverse kinematics, KDL by
   default). OMPL (RRTConnect) then finds a collision-free joint-space path to one of them. The path is
   time-parameterised against the joint velocity and acceleration limits, scaled by `--velocity` and `--acceleration`.
4. **Execution.** move_group sends the trajectory to the driver's `scaled_joint_trajectory_controller` (a
   `FollowJointTrajectory` action). With mock hardware the commanded positions are copied straight to the joint states.
   On the real robot the driver streams them to the UR controller.
5. **Feedback.** The script waits for the result. It then reads `base_link → tool0` from TF and prints the pose
   actually reached, so you can compare it with the goal.

The script only talks to the standard `/move_action` interface. The same script works for mock hardware, Isaac Sim and
the real robot. Only what's running behind move_group changes.

## 4. Limitations: when it breaks

- **Unreachable goals.** Goals beyond about 0.85 m, too close to the base, or with an orientation the wrist can't reach
  at that point make planning fail (reported as `FAILURE`). The 0.85 m check is only a warning. Real
  reachability depends on orientation too.
- **The path is not a straight line.** OMPL plans in joint space. The tool can swing along a curved path to the goal,
  and on a real cell that path can be surprising.
- **No custom collision objects.** Only the robot's own links are avoided. A table, a fixture or a person isn't in the planning scene, so the planner will happily go through them.
- **Random planner.** RRTConnect is sampling-based. The same goal can give different paths, and the arm can end in a
  different IK solution (elbow up/down, wrist flipped) than you expect.
- **Singularities and joint limits.** Goals near a wrist singularity (wrist 2 ≈ 0) or near ±360° joint limits can fail,
  or produce large joint motions for a small change in pose.
- **Tolerances.** The goal is "reached" within 1 mm / 0.57° by default, not exactly. Tightening the tolerances further
  makes IK slower and less reliable.
- **Roll/pitch/yaw.** RPY has a singularity at pitch = ±90°, so different RPY triples can describe the same orientation.
  The printed RPY of the reached pose can look different from what you typed while the orientation is the same. The
  quaternion is the unambiguous reference.
- **Blocking.** The prompt blocks while the robot moves. There's no way to pre-empt a motion from the prompt, other
  than Ctrl-C, which also stops the script.
- **TF frame.** The goal is for `tool0` (the flange), not the tip of a gripper. Use `--ee-link` if a tool link is in
  the URDF.

## 5. Running on the real UR5e

The script stays the same. Only the driver launch changes:

```bash
ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur5e robot_ip:=<ROBOT_IP> launch_rviz:=false
ros2 launch ur_moveit_config ur_moveit.launch.py ur_type:=ur5e launch_rviz:=true
ros2 run ur5e_pose_commander pose_commander
```

What changes:

- **External Control URCap.** The teach pendant must run the *External Control* program pointing at this PC, and the
  robot must be in remote control mode. Otherwise the controller accepts trajectories but the arm doesn't move.
- **Calibration.** Every UR robot has factory kinematic calibration that differs slightly from the nominal URDF. Without
  extracting it (`ur_calibration`) and passing it as `kinematics_params_file`, poses are off by a few millimetres.
- **Real dynamics.** Mock hardware follows the trajectory perfectly. The real arm has tracking error and payload
  effects, and it stops on violations: protective stop on collision, joint limits or safety planes. A goal that works in
  RViz can trigger a protective stop on the real robot.
- **Speed scaling.** The teach pendant's speed slider and the safety system scale the trajectory in real time
  (`scaled_joint_trajectory_controller`). Motion can take longer than planned, or pause.
- **The environment isn't modelled.** Add the table, walls and tools to the planning scene before running, or the
  planner will drive the arm into them. Start with low `--velocity` / `--acceleration` (for example 0.1), keep a hand
  on the e-stop, and preview with `--plan-only` first.
- **Network/real-time.** The driver needs a stable, low-latency Ethernet link. Dropped packets abort the trajectory.
  A real-time kernel is recommended.
- **Payload/TCP.** Set the actual payload and TCP on the robot so that the controller and the safety limits match the
  tool being carried.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `move_group is not running` | Start `ur5e_mock.launch.py` first and wait for `You can start planning now!`. Check that both terminals have the same `ROS_DOMAIN_ID` |
| `Planning group '...' does not exist` | Wrong `--group` for the running MoveIt config. Leave it out and let the script pick |
| `Failed: FAILURE` | Goal unreachable: move it closer, or change the orientation (for example `180 0 0` = pointing down) |
| `Failed: CONTROL_FAILED` | The controller rejected or aborted the trajectory. Check `ros2 control list_controllers` (`scaled_joint_trajectory_controller` must be `active`) |
| `Cannot read current pose` | TF isn't available yet. Wait a moment after starting the driver |
