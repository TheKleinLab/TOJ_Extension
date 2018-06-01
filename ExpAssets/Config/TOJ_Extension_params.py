## KLibs Parameter overrides ##

from klibs import P

# All of these values can be overridden locally in a file here:
# ExpAssets/Local/TOJ_Extension_params.py
# You will need to create it if it doesn't already exist.

#########################################
# Runtime Settings
#########################################
collect_demographics = True
manual_demographics_collection = False
manual_trial_generation = False
run_practice_blocks = True
multi_user = False
view_distance = 57 # in centimeters, 57cm = 1 deg of visual angle per cm of screen

#########################################
# Available Hardware
#########################################
eye_tracker_available = False
eye_tracking = False
labjack_available = False
labjacking = False

#########################################
# Environment Aesthetic Defaults
#########################################
default_fill_color = (45, 45, 45, 45)
default_color = (255, 255, 255, 255)
default_font_size = 0.5
default_font_unit = 'deg'
default_font_name = 'Frutiger'

#########################################
# EyeLink Settings
#########################################
manual_eyelink_setup = False
manual_eyelink_recording = False

saccadic_velocity_threshold = 20
saccadic_acceleration_threshold = 5000
saccadic_motion_threshold = 0.15

#########################################
# Experiment Structure
#########################################
multi_session_project = False
trials_per_block = 240
blocks_per_experiment = 2
table_defaults = {}
conditions = ['first', 'second']

#########################################
# Development Mode Settings
#########################################
dm_auto_threshold = True
dm_trial_show_mouse = True
dm_ignore_local_overrides = False
dm_show_gaze_dot = True

#########################################
# Data Export Settings
#########################################
primary_table = "trials"
unique_identifier = "userhash"
default_participant_fields = [[unique_identifier, "participant"], "gender", "age", "handedness"]
default_participant_fields_sf = [[unique_identifier, "participant"], "random_seed", "gender", "age", "handedness"]

#########################################
# EXPERIMENT-SPECIFIC PARAMS
#########################################
use_numpad = True # If False, use regular 2/8 instead of numpad 2/8 for responses
judgement_type = "first" if P.condition == None else P.condition
initial_probe_bias = "LEFT" # Which probe bias to have first (either "LEFT" or "RIGHT")
trials_per_practice_block = 40