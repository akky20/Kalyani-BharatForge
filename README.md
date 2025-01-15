# Kalyani-BhartaForge: Centralised Inteligence for Dynamic Swarm Navigation

## Project Description
Its is an autonomous multi-robot system developed using ROS 2 Humble. This project utilizes TurtleBot3 Burger robots for autonomous navigation, communication, and reinforcement learning-based decision-making. The system supports both master-slave swarm architecture and independent robotic operations.

---

## Dependencies
Ensure you have the following ROS 2 Humble packages installed:

- `ros-humble-turtlebot3*`
- `ros-humble-navigation2`
- `ros-humble-slam-toolbox`
- `ros-humble-gazebo-ros-pkgs`
- `ros-humble-rviz2`

You can install all dependencies automatically using the following command:

```bash
sudo apt update && sudo apt install -y \
ros-humble-turtlebot3* \
ros-humble-navigation2 \
ros-humble-slam-toolbox \
ros-humble-gazebo-ros-pkgs \
ros-humble-rviz2
```

---

## Project Structure
The repository contains the following key directories:

1. **autobot_recog**: Contains all launch files and node scripts for running the robot system.
2. **communication_msgs**: Contains service and client scripts for inter-robot communication.
3. **RL**: Contains reinforcement learning algorithms for TD3 and PPO.
4. **object_detection**: Contain code files for object detection model.

---

## Getting Started

### 1. Build the Workspace
Ensure you are in the root of your ROS 2 workspace, then execute the following commands:

```bash
colcon build
source install/setup.bash
```

### 2. Launch the Autonomous System

#### Independent Robot Operation
To start the complete autonomous system, run:

```bash
ros2 launch autobot_recog bots_launch.launch.py
```

#### Master-Slave Swarm Architecture
For a master-slave architecture, execute:

```bash
ros2 launch autobot_recog master_slave.launch.py
```

---

### 3. Reinforcement Learning Training

Navigate to the RL directory and choose the desired algorithm for training:

#### PPO Training
```bash
cd RL/ppo
python3 train_ppo.py
```

#### TD3 Training
```bash
cd RL/td3
python3 train_velodyne_node.py
```

---

### 4. YOLO Object Detection Training

Before running the training script, ensure the dataset is prepared. A dummy dataset is included in the repository for reference. To train the YOLO model, run:

```bash
cd object_detection
python3 training_yolo.py
```

---

### 5. Video Demonstration 
1. 
https://github.com/user-attachments/assets/cfd96fc7-19fe-42fd-b517-a0da61f034db


2. 
https://github.com/user-attachments/assets/c92a085f-4eac-493c-a3a1-2b72b9b46ce8

3. 
https://github.com/user-attachments/assets/d6296f39-f8d9-4bab-ad03-3aa6750578bd

4. 
https://github.com/user-attachments/assets/74a02287-bb27-44b8-b657-55c78f372924


## Notes


- Make sure to source your workspace after every build using:
  ```bash
  source install/setup.bash
  ```

- Customize `bots_launch.launch.py` and `master_slave.launch.py` as per your application needs.

- The RL folder contains examples for TD3 and PPO implementations. Modify the scripts for specific tasks.

---

## Contribution
Contributions are welcome! Please follow the standard fork-and-pull workflow:
1. Fork the repository.
2. Create a new branch.
3. Commit your changes.
4. Push to your fork.
5. Submit a pull request.


Happy robotics! :robot:


