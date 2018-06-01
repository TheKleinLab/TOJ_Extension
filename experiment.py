__author__ = "jon mulle"


# Import required KLibs libraries
import klibs
from klibs.KLConstants import STROKE_INNER, TK_S, NA, RC_COLORSELECT, RC_KEYPRESS
from klibs import P
from klibs.KLUtilities import *
from klibs.KLKeyMap import KeyMap
from klibs.KLUserInterface import any_key, ui_request
from klibs.KLGraphics import fill, blit, flip, clear
from klibs.KLGraphics.KLDraw import Asterisk, Line, Rectangle, Ellipse, ColorWheel
from klibs.KLGraphics.colorspaces import const_lum as colors
from klibs.KLEventInterface import TrialEventTicket as ET
from klibs.KLCommunication import message

# Import required external libraries
import sdl2
import time
import random

# Define some useful constants
LEFT = "LEFT"
RIGHT = "RIGHT"
PROBE = "PROBE"
TARGET = "TARGET"
VERTICAL = "VERTICAL"
HORIZONTAL = "HORIZONTAL"
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)


class TOJ_Extension(klibs.Experiment):

	# probe location distributions
	probe_pos_bias_freq = 0.8
	probe_neg_bias_freq = 0.2

	# timing
	target_onset = 500 # ms
	t1_offset_constant = 1380 # ms
	block_message_display_interval = 3 # sec

	# dynamic vars
	probe_color = None
	probe_angle = None
	probe_locs = None
	probe_loc = None  # english string (left/right)
	probe_pos = None  # coordinate tuple
	target_loc = None  # as LEFT or RIGHT, ie. for data
	target_1_loc = None
	target_2_loc = None
	t1 = None
	t2 = None


	def setup(self):
		
		# Stimulus sizes
		line_len = deg_to_px(3.0)
		fixation_size = deg_to_px(1.0)
		fixation_stroke = deg_to_px(0.1)
		box_size = deg_to_px(4.0)
		box_stroke = deg_to_px(0.2)
		probe_size = deg_to_px(0.45)
		wheel_size = deg_to_px(10.8)
		
		# Stimulus Drawbjects
		self.fixation = Asterisk(fixation_size, thickness=fixation_stroke, fill=WHITE).render()
		self.box = Rectangle(box_size, stroke=[box_stroke, WHITE, STROKE_INNER]).render()
		self.h_line = Line(line_len, WHITE, box_stroke, 90)
		self.v_line = Line(line_len, WHITE, box_stroke)
		self.probe = Ellipse(probe_size)
		self.wheel = ColorWheel(wheel_size, thickness=wheel_size/8)
		self.wheel_disc = Ellipse(int(wheel_size*0.75), fill=BLACK) # to mimic old-style color wheel

		# Layout of stimuli
		box_offset = deg_to_px(9.25)
		self.box_l_pos = (P.screen_c[0]-box_offset, P.screen_c[1])
		self.box_r_pos = (P.screen_c[0]+box_offset, P.screen_c[1])
		self.probe_pos_bias_loc = P.initial_probe_bias
		self.probe_neg_bias_loc = LEFT if P.initial_probe_bias == "RIGHT" else RIGHT

        # Initialize ResponseCollector keymap
		if P.use_numpad:
			keysyms = [sdl2.SDLK_KP_8, sdl2.SDLK_KP_2]
		else:
			keysyms = [sdl2.SDLK_8, sdl2.SDLK_2]

		self.toj_keymap = KeyMap(
			"toj_responses", # Name
			['Keypad 8', 'Keypad 2'], # UI labels
			[VERTICAL, HORIZONTAL], # Data labels
			keysyms # SDL2 Keysyms
		)
        
		# Generate text for trial messages
		self.txtm.add_style('probe_bias', '0.5deg', color=[20, 180, 220, 255])

		toj_string = "Which line appeared {0}?\n (Vertical = Keypad 8   Horizontal = Keypad 2)"
		self.toj_msg = message(toj_string.format(P.judgement_type), align='center', blit_txt=False)
		self.color_judgement_m = message('Choose a color.', blit_txt=False)
		self.trial_start_message = message("Press space to continue", "default", blit_txt=False)
        
		# Insert TOJ-only (1) and probe-only (2, 4) practice blocks
		if P.run_practice_blocks:
			num = P.trials_per_practice_block
			self.insert_practice_block(1, trial_counts=num, factor_mask={"trial_type": "TARGET"})
			self.insert_practice_block(2, trial_counts=num, factor_mask={"trial_type": "PROBE"})
			self.insert_practice_block(4, trial_counts=num, factor_mask={"trial_type": "PROBE"})


	def block(self):
		
		# After first experimental block, switch probe bias to the other side
		second_half = P.block_number > 3 if P.run_practice_blocks else P.block_number > 1
		if second_half:
			self.probe_neg_bias_loc = self.probe_pos_bias_loc
			self.probe_pos_bias_loc = LEFT if self.probe_pos_bias_loc == RIGHT else RIGHT

		# if it's a non-practice block, determine the  subset of the block's trials that will be 
		# probe trials (1/3rd by default), and how many of those will be at each location.
		t_count = len(self.blocks[P.block_number - 1])
		if not P.practicing:
			trial_type_factors = self.trial_factory.exp_factors['trial_type']
			t_count *= trial_type_factors.count('PROBE') / float(len(trial_type_factors))
		pos_probe_trials = [self.probe_pos_bias_loc] * int(t_count * self.probe_pos_bias_freq)
		neg_probe_trials = [self.probe_neg_bias_loc] * int(t_count * self.probe_neg_bias_freq)
		self.probe_locs = pos_probe_trials + neg_probe_trials
		random.shuffle(self.probe_locs)
		
		# Generate block start messages and display them before the next block.
		progress_str = "Block {0} of {1}".format(P.block_number, P.blocks_per_experiment)
		if P.practicing:
			progress_str += "\n(This is a practice block.)"
		progress_msg = message(progress_str, 'default', align='center', blit_txt=False)

		probe_str1 = ("During this block, the colored disk will appear more often on the:\n\n"
			"and less often on the:\n")
		probe_str2 = "\n{0}\n\n{1}".format(self.probe_pos_bias_loc, self.probe_neg_bias_loc)
		probe_msg1 = message(probe_str1, align='center', blit_txt=False)
		probe_msg2 = message(probe_str2, 'probe_bias', align='center', blit_txt=False)

		start = time.time()
		while time.time() - start < self.block_message_display_interval:
			fill()
			ui_request()
			blit(progress_msg, 8, (P.screen_c[0], 50))
			if not (P.run_practice_blocks and P.block_number == 1):
				blit(probe_msg1, 5, P.screen_c)
				blit(probe_msg2, 5, P.screen_c)
			flip()

		flush()
		message("Press any key to start.", registration=5, location=[P.screen_c[0], P.screen_y*0.8])
		flip()
		any_key()


	def setup_response_collector(self):
        
		# Configure response collector based on trial type
		self.rc.terminate_after = [10, TK_S]
		if self.trial_type == PROBE:
			self.rc.uses(RC_COLORSELECT)
			self.rc.display_callback = self.color_judgement
			self.rc.color_listener.set_wheel(self.wheel)
			self.rc.color_listener.set_target(self.probe)
			self.rc.color_listener.interrupts = True
		else:
			self.rc.uses(RC_KEYPRESS)
			self.rc.display_callback = self.toj_judgement
			self.rc.keypress_listener.key_map = self.toj_keymap
			self.rc.keypress_listener.interrupts = True


	def trial_prep(self):

		# Determine target orientations and orders, and probe location (if probe trial)
		self.target_1_loc = self.box_l_pos if self.target_loc == LEFT else self.box_r_pos
		self.target_2_loc = self.box_r_pos if self.target_loc == LEFT else self.box_l_pos
		self.t1 = self.v_line.render() if self.first_target == VERTICAL else self.h_line.render()
		self.t2 = self.h_line.render() if self.first_target == VERTICAL else self.v_line.render()
		self.probe_loc = self.probe_locs.pop() if self.trial_type == PROBE else NA
		self.probe_pos = self.box_l_pos if self.probe_loc == LEFT else self.box_r_pos

		# Randomize wheel rotation, and randomly choose probe colour from wheel
		self.wheel.rotation = int(random.uniform(0, 360))
		self.wheel.render()
		self.probe_angle = int(random.uniform(0, 360))
		self.probe_color = colors[self.probe_angle]
		self.probe.fill = self.probe_color
		self.probe.render()

		# Determine the time-course of events during the trial
		random_offset = random.randint(1, 27) * (1000.0/60) # between 16.7 ms and 450 ms
		events = [[self.t1_offset_constant + random_offset, 'target_1_on']]
		events.append([events[-1][0] + 200, 'probe_off']) 
		events.append([events[-2][0] + self.soa, 'target_2_on'])
		events.append([events[-1][0] + 300, 'target_2_off'])
		for e in events:
			self.evm.register_ticket(ET(e[1], e[0]))

		# If not first trial of block, display message and start trial on keypress
		if P.trial_number > 1:
			fill()
			blit(self.trial_start_message, registration=5, location=P.screen_c)
			flip()
			any_key()


	def trial(self):

		# Display trial stimuli in sequence, based on events defined in trial_prep
		while self.evm.before('target_2_off', pump_events=True):
			self.display_refresh(False)
			if self.evm.after('target_2_on'):
				blit(self.t2, location=self.target_2_loc, registration=5)
			if self.evm.after('target_1_on'):
				blit(self.t1, location=self.target_1_loc, registration=5)
				if self.trial_type == PROBE and self.evm.before('probe_off'):
					blit(self.probe, location=self.probe_pos, registration=5)
			flip()

		# Show display callback and wait for response (probe or TOJ, depending on trial)
		self.rc.collect()

		# Clear screen immediately after response made or timeout
		fill()
		flip()

		# Process collected response before logging trial data to database
		if self.trial_type == PROBE:
			probe_rt = self.rc.color_listener.response(False, True)
			selected_angle = self.rc.color_listener.response(True, False)
			selected_color = colors[int(selected_angle)]
			probe_judgement_diff = int(self.probe_angle) - selected_angle
			toj_rt, toj_response = [NA, NA]
		else:
			toj_rt = self.rc.keypress_listener.response(False, True)
			toj_response = self.rc.keypress_listener.response(True, False)
			probe_rt, selected_angle, selected_color, probe_judgement_diff = [NA, NA, NA, NA]

		return {
			"block_num": P.block_number,
			"trial_num": P.trial_number,
			"trial_type": self.trial_type,
			"toj_judgement_type": P.judgement_type,
			"block_bias": self.probe_pos_bias_loc,
			"soa": self.soa,
			"rotation": self.wheel.rotation,
			"probe_initial_bias": P.initial_probe_bias,
			"probe_loc": self.probe_loc if self.trial_type == PROBE else NA,
			"probe_color": self.probe_color if self.trial_type == PROBE else NA,
			"probe_angle": int(self.probe_angle) if self.trial_type == PROBE else NA,
			"probe_judgement": selected_angle,
			"probe_judgement_color": selected_color,
			"p_minus_j": probe_judgement_diff,
			"probe_rt": probe_rt,
			"t1_loc": self.target_loc,
			"t1_type": self.first_target,
			"toj_judgement": toj_response,
			"toj_rt": toj_rt
		}


	def trial_clean_up(self):
		pass


	def clean_up(self):
		pass


	def display_refresh(self, flip=True):
		fill()
		blit(self.box, location=self.box_l_pos, registration=5)
		blit(self.box, location=self.box_r_pos, registration=5)
		blit(self.fixation, location=P.screen_c, registration=5)
		if flip:
			flip()

	def toj_judgement(self):
		fill()
		blit(self.toj_msg, 5, P.screen_c)
		flip()

	def color_judgement(self):
		fill()
		blit(self.wheel, location=P.screen_c, registration=5)
		blit(self.wheel_disc, 5, P.screen_c)
		blit(self.color_judgement_m, 5, P.screen_c)
		flip()