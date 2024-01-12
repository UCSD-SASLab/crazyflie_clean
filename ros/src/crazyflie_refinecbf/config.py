# Configuration file used to define key parameters for RefineCBF Experimentation

print("Loading Config File...")

# Generic Python Imports
import numpy as np
import jax.numpy as jnp
import time
import matplotlib.pyplot as plt
import pickle
import logging

# ROS Imports
import rclpy
from rclpy.qos import QoSProfile
from geometry_msgs.msg import Twist, TransformStamped, PoseStamped
from nav_msgs.msg import Odometry, Path
from std_msgs.msg import Bool, Float32

# RefineCBF Imports
import refine_cbfs
import hj_reachability as hj
from refine_cbfs.dynamics import HJControlAffineDynamics
from cbf_opt import ControlAffineDynamics, ControlAffineCBF, ControlAffineASIF
from refine_cbf.utils import *
from refine_cbf.experiment_obstacles import Obstacles
from crazyflie_msgs.msg import PositionVelocityStateStamped

# Save location of experiment data (written to in safety_filter.py, or nominal_policy.py if USE_UNFILTERED_POLICY = True)
#DATA_FILENAME = './experiment_dataset.txt'

# Hardware Experiment
# If True, transformstamped to odom node will run to allow communication between state feedback in Vicon arena and Rviz (trajectory would not show otherwise)
HARDWARE_EXPERIMENT = False

# State Feedback Topic Name (Gazebo: 'gazebo/odom', Turtlebot3: 'odom', VICON: 'vicon/turtlebot/turtlebot')
STATE_FEEDBACK_TOPIC = 'gazebo/odom'
# STATE_FEEDBACK_TOPIC = 'odom'
# STATE_FEEDBACK_TOPIC = 'vicon/robot_1/robot_1'

# Use unfiltered policy (i.e. only nominal/safety agnostic control applied): True or False
# used in the refine_cbf_launch.py and nominal_policy.py
# If True, this will publish the /cmd_vel topic straight from the nominal policy node instead of the safety filter node
# Run data will not be saved to a the typical data file if this is True (will be found in DATA_FILENAME_NOMINAL_POLICY).
USE_UNFILTERED_POLICY = False

# Use a manually controller for the nominal policy: True or False
USE_MANUAL_CONTROLLER = False

# Refine the CBF: True or False
# If this is False, the final converged CBF will be used in the safety filter and not refined
USE_REFINECBF = True

# Refine CBF Iteration Time Step (dt)
TIME_STEP = 0.15 # default is 0.15

# Initial State / Pose
INITIAL_STATE = np.array([0.5, 1.0, 0])

# Safety Filter ROS Node Timer
SAFETY_FILTER_TIMER_SECONDS = 0.033
SAFETY_FILTER_QOS_DEPTH = 10

# Nominal Policy ROS Node Timer
NOMINAL_POLICY_TIMER_SECONDS = 0.033
NOMINAL_POLICY_QOS_DEPTH = 10

## NOMINAL POLICY TABLE !!!!!!!!!!!!!!!!TODO!!!!!!!!!!!!!!!!!!!!!
# Insert the filename of the nominal policy table numpy file, that was precomputed.
NOMINAL_POLICY_FILENAME = './nominal_policy_table.npy'

## HAMILTON JACOBI REACHABILITY GRID

# Density of grid
# tuple of size equal to state space dimension that defines the number of grid points in each dimension
# For example, a differential drive dynamics robot will have a 3D state space (x, y, theta)
#For crazyflie, we'd likely use (x,z,pitch), so still 3D 
#Uncertain whether the dynamic model would be represented by thrust 1 and thrust 2.
# NOTE: This resolution must be the same as the resolution used to generate the nominal policy table (if using a nominal policy table)
GRID_RESOLUTION = (61, 61, 61)

# Lower and upper bounds of the discretized state space
# numpy array with dimensions equal to state space dimension
# For example, a differential drive dynamics robot will have a 3D state space and the resulting numpy array will be of size (3,)
GRID_LOWER = np.array([0., 0., -np.pi])
GRID_UPPER = np.array([2., 2., np.pi])

# Periodic dimensions
# A single integer or tuple of integers denoting which dimensions are periodic in the case that
# the `boundary_conditions` are not explicitly provided as input.
# For example, a differential drive dynamics robot will have a 3D state space (x, y, theta), where theta is periodic, which is the third dimension (index 2)
PERIODIC_DIMENSIONS = 2

# State Domain
STATE_DOMAIN = hj.sets.Box(lo=GRID_LOWER, hi=GRID_UPPER)

# State Space Grid
GRID = hj.Grid.from_lattice_parameters_and_boundary_conditions(STATE_DOMAIN, GRID_RESOLUTION, periodic_dims=PERIODIC_DIMENSIONS)

## CONTROL SPACE

# Control space parameters
# two arrays with size of the control space dimension that define the lower and upper bounds of the control space
# For instance, a differential drive dynamics robot will have a 2D control space (v, omega) and if
# using a Turtlebot3 Burger, a control space could be bounded by v_min = 0.1, v_max = 0.21, omega_max/omega_min = +/- 1.3
# NOTE: The full control range of a TB3 burger is v_min = 0.0, v_max = 0.21, omega_max/omega_min = +/- 2.63
#       However, if the resulting controller is bang-bang-like, the angular velocity bound must be dropped to around 1.3 rad/s magnitude.

U_MIN = np.array([0.0, 0.0]) #For planar quadcopter, u=[T1, T2]
U_MAX = np.array([1.0, 1.0])

## DISTURBANCE SPACE

# Disturbance space parameters
# two arrays with size of the disturbance space dimension that define the lower and upper bounds of the disturbance space
# For instance, a differential drive dynamics robot will have a 2D disturbance space (v_disturbance, omega_disturbance) and if
# using a Turtlebot3 Burger, the disturbance space will be bounded by v_disturbance_min = -0.1, v_disturbance_max = 0.1, omega_disturbance_max/omega_disturbance_min = +/- 0.1
# NOTE: Unused in this package, but is here if needed.

W_MIN = np.array([-0.1, -0.1])
W_MAX = np.array([0.1, 0.1])

## DYNAMICS TODO Likely will have to change this part
#Need to change the DiffDriveDynamics 
DYNAMICS = DiffDriveDynamics({"dt": 0.05}, test=False)  # dt is an arbitrary value choice, as the dynamics object requires a dt 
                                                        # value for its constructor argument but it is not used for this package

DYNAMICS_JAX_NUMPY = DiffDriveJNPDynamics({"dt": 0.05}, test=False) # dt is an arbitrary value choice, as the dynamics object requires a dt 
                                                                    # value for its constructor argument but it is not used for this package

DYNAMICS_HAMILTON_JACOBI_REACHABILITY = HJControlAffineDynamics(DYNAMICS_JAX_NUMPY, control_space=hj.sets.Box(jnp.array(U_MIN), jnp.array(U_MAX)))

DYNAMICS_HAMILTON_JACOBI_REACHABILITY_WITH_DISTURBANCE = HJControlAffineDynamics(DYNAMICS_JAX_NUMPY, control_space=hj.sets.Box(jnp.array(U_MIN), jnp.array(U_MAX)), disturbance_space=hj.sets.Box(jnp.array(W_MIN), jnp.array(W_MAX)))

## CONTROL BARRIER FUNCTION (CBF)

# Precomputed CBF Filename - if not using RefineCBF (i.e. USE_REFINECBF = False), this will be the CBF used in the safety filter CBF-QP
PRECOMPUTED_CBF_FILENAME = './precomputed_cbf.npy'

# Experiment CBF Filename: Location where a dictionary of each CBF iteration will be saved to - can be used analyze CBF in post
EXPERIMENT_CBF_FILENAME = './experiment_cbf.pkl'

# Gamma value / discount rate for the CBVF - affects how quickly system can exponentially approach boundary of the safe set
# A higher gamma value will make the safety control more aggressive, while a lower gamma value will make the safety control more conservative.
# With gamma = 0 resulting in extreme conservativeness, where the resulting trajectories will not take a form which drops below the initial safety value.
GAMMA = 0.25

# Scalar multiplier for the CBF - linear multiplier for values of the CBF.
# NOTE: Should rarely need to change this, but it is here if needed.
CBF_SCALAR = 1.0

# Initial CBF Parameters
RADIUS_CBF = 0.33 # radius of the circular CBF
CENTER_CBF = np.array([0.5, 1.0]) # center of the circular CBF

# CBF Object
CBF = DiffDriveCBF(DYNAMICS, {"center": CENTER_CBF, "r": RADIUS_CBF, "scalar": CBF_SCALAR}, test=False)

# Creating the Initial CBF
diffdrive_cbf = CBF # instatiate a diffdrive_cbf object with the Differential Drive dynamics object
diffdrive_tabular_cbf = refine_cbfs.TabularControlAffineCBF(DYNAMICS, dict(), grid=GRID)
diffdrive_tabular_cbf.tabularize_cbf(diffdrive_cbf) # tabularize the cbf so that value can be calculated at each grid point
INITIAL_CBF = diffdrive_tabular_cbf.vf_table # initial CBF

## CONSTRAINT SET / OBSTACLES

OBSTACLES = Obstacles()

# List of obstacle sets
OBSTACLE_LIST = OBSTACLES.get_obstacle_list()

# When to update obstacles, size of the list must be n-1, where n is the number of obstacle sets.
OBSTACLE_ITERATION_LIST = OBSTACLES.get_iteration_list()

# padding around the obstacle in meters
# float that inflates the obstacles by a certain amount using Minkoswki sum
# For example, if the maximum radius of a robot is 0.15 m, the padding should be at least 0.15 m
OBSTACLE_PADDING = 0.11

## Goal Set

# Goal Set Parameters, used in refine_cbf_visualization.py
GOAL_SET_RADIUS = 0.10
GOAL_SET_CENTER = np.array([1.5, 1.0])