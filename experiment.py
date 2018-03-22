__author__ = "jon mulle"

import klibs
from klibs.KLConstants import *
from klibs import P
from klibs.KLUtilities import *
from klibs.KLKeyMap import KeyMap
from klibs.KLUserInterface import any_key
from klibs.KLGraphics import fill, blit, flip, clear
from klibs.KLGraphics.KLDraw import Asterisk, Line, Rectangle, Ellipse, ColorWheel
from klibs.KLGraphics.colorspaces import const_lum as colors
from klibs.KLEventInterface import TrialEventTicket as ET
from klibs.KLCommunication import message

import sdl2
import time
import random
from random import choice

LEFT = "LEFT"
RIGHT = "RIGHT"
PROBE = "PROBE"
TARGET = "TARGET"
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
VERTICAL = "VERTICAL"
HORIZONTAL = "HORIZONTAL"


class TOJ_Extension(klibs.Experiment):
	# graphical elements
	background = None
	line_len_dv = 3
	h_line = None
	v_line = None
	box = None
	box_border_color = WHITE
	box_border_stroke = 8  # px
	box_size_dva = 4
	box_l_pos = None
	box_r_pos = None
	fixation = None
	fixation_size_dva = 1
	wheel_prototype = None
	probe_prototype = None
	probe = None
	probe_size_dv = 1
	probe_pos_bias_loc = None
	probe_neg_bias_loc = None
	probe_pos_bias_freq = 0.8
	probe_neg_bias_freq = 0.2
	color_list = None
	toj_judgement_m = None  # pre-rendered message
	color_judgement_m = None  # ditto
	trial_start_message = None
	cursor_dot = None
	response_collector_keymapping = (['Key Pad 8', 'Key Pad 2'], [VERTICAL, HORIZONTAL], [sdl2.SDLK_KP_8, sdl2.SDLK_KP_2])
	toj_judgement_string = "Which line appeared {0}?\n (Vertical = {1}   Horizontal = {2})"

	# timing
	target_onset = 500  # ms
	t1_offset_constant = 1380  # ms
	block_message_display_interval = 3

	# dynamic vars
	block_strings = None  # dict of all possible block messages rendered in setup for speed and to avoid sdl2_ttf errors
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
	wheel = None
	reblocked = 0


	def __init__(self, *args, **kwargs):
		super(TOJ_Extension, self).__init__(*args, **kwargs)

	def setup(self):
		hide_mouse_cursor()
		clear()
        
		self.box_l_pos = (P.screen_x // 3, P.screen_c[1])
		self.box_r_pos = (2 * P.screen_x // 3, P.screen_c[1])
		self.h_line = Line(deg_to_px(self.line_len_dv), self.box_border_color, self.box_border_stroke, 90)
		self.v_line = Line(deg_to_px(self.line_len_dv), self.box_border_color, self.box_border_stroke)
		self.probe_pos_bias_loc = P.initial_probe_pos_bias_loc  # allows block-level toggling without inverting initial value
		self.probe_neg_bias_loc = LEFT if P.initial_probe_pos_bias_loc == "RIGHT" else RIGHT  # allows block-level toggling without inverting initial value
        
		self.box = Rectangle(deg_to_px(self.box_size_dva), stroke=[self.box_border_stroke, self.box_border_color, STROKE_INNER]).render()
		self.fixation = Asterisk(deg_to_px(self.fixation_size_dva), thickness=4, fill=WHITE)
		self.probe = Ellipse(20)  # NOT dv in the baseball original, alas
		self.wheel = ColorWheel(500, thickness=62)
		self.wheel_disc = Ellipse(376, fill=BLACK) # to mimic old-style color wheel
        
		self.txtm.add_style('probe_bias', 28, [20, 180, 220, 255])
		self.txtm.add_style('small', 14, [255, 255, 255, 255])
		self.color_judgement_m = message('Choose a color.', blit_txt=False)
		self.trial_start_message = message("Press space to continue", "default", blit_txt=False)
		self.toj_judgement_m = message(self.toj_judgement_string.format(P.toj_judgement, *self.response_collector_keymapping[0]), blit_txt=False)
        
		self.insert_practice_block(1, trial_counts=40, factor_mask={"trial_type": "TARGET"})
		self.insert_practice_block(2, trial_counts=40, factor_mask={"trial_type": "PROBE"})
		self.insert_practice_block(4, trial_counts=40, factor_mask={"trial_type": "PROBE"})

		def block_msg(block_num, pos_bias, neg_bias): 
			r_strs = []
			pump()
			def_size = self.txtm.styles['default'].font_size
			bias_size = self.txtm.styles['probe_bias'].font_size
			msg_y = 50
			blocks_remaining_str = "Block {0} of {1}".format(block_num, P.blocks_per_experiment)
			r_strs.append([message(blocks_remaining_str, 'default', registration=5, blit_txt=False), [P.screen_c[0], msg_y]])
			msg_y += 2 * def_size
			if block_num in (1,2,4):
				r_strs.append([message("(This is a practice block.)", 'default', blit_txt=False), [P.screen_c[0], msg_y]])
			msg_y = int(P.screen_c[1] - 0.5 * (5 * def_size + bias_size))
			if i != 1:
				probe_strings = ["During this block, the colored disk will appear more often on the:",
								 "and less often on the:"]
				r_strs.append([message(probe_strings[0], blit_txt=False), [P.screen_c[0], msg_y]])
				msg_y += 2 * def_size
				r_strs.append([message(pos_bias, 'probe_bias',blit_txt=False), [P.screen_c[0], msg_y]])
				msg_y += def_size + bias_size
				r_strs.append([message(probe_strings[1], 'default', blit_txt=False),[P.screen_c[0], msg_y]])
				msg_y += 2 * def_size
				r_strs.append([message(neg_bias, 'probe_bias', blit_txt=False), [P.screen_c[0], msg_y]])
			return r_strs

		self.block_strings = {}
		for i in range(1, 6):
			for bias in [LEFT,RIGHT]:
				n_bias = LEFT if bias == RIGHT else RIGHT
				self.block_strings["b_{0}_pro_{1}".format(i, bias)] = block_msg(i, bias, n_bias)

	def block(self):
		if P.block_number != 1:
				if P.block_number == 4: # immediately after each probe-trial practice, repeat probe bias
					self.probe_neg_bias_loc = self.probe_pos_bias_loc
					self.probe_pos_bias_loc = LEFT if self.probe_pos_bias_loc == RIGHT else RIGHT

		fill()
		# make sure there are enough of these to finish the block AND that this doesn't apply during practice blocks
		t_count = P.trials_per_block if P.block_number in (3, 5) else len(self.blocks[P.block_number - 1])

		# if it's a non-practice block, get the subset of the block's trials that will be probed trials
		if P.block_number in (3, 5):
			t_count *= P.target_probe_trial_dist[PROBE] / sum(P.target_probe_trial_dist.values())
		pos_probe_trials = [self.probe_pos_bias_loc] * int(t_count * self.probe_pos_bias_freq)
		neg_probe_trials = [self.probe_neg_bias_loc] * int(t_count * self.probe_neg_bias_freq)
		self.probe_locs = pos_probe_trials + neg_probe_trials
		random.shuffle(self.probe_locs)

		# def test_probe_dist():
		# 	pos_probes_shuffled = self.probe_locs.count(LEFT)
		# 	neg_probes_shuffled = self.probe_locs.count(RIGHT)
		# 	pos_probes_correct = all([i == self.probe_pos_bias_loc for i in pos_probe_trials])
		# 	neg_probes_correct = all([i == self.probe_neg_bias_loc for i in neg_probe_trials])
		# 	vars = [t_count, len(pos_probe_trials), len(neg_probe_trials), pos_probes_correct, neg_probes_correct, P.block_number, pos_probes_shuffled, neg_probes_shuffled, len(self.blocks[P.block_number - 1])]
		# 	print "Block: {5} ({8}) t_count: {0}\t\t pos_probe_trials: {1}->{6} ({3})\t\t neg_probe_trials: {2}->{7} ({4})".format(*vars)
		# 	P.block_number +=1
		# 	if P.block_number == 6:
		# 		self.reblocked += 1
		# 		if self.reblocked == 10:
		# 			self.quit()
		# 		P.block_number = 1
		# test_probe_dist()
		# return self.block()

		start = time.time()
		while time.time() - start < self.block_message_display_interval:
			fill()
			pump()
			for m in self.block_strings["b_{0}_pro_{1}".format(P.block_number, self.probe_pos_bias_loc)]:
				blit(m[0], 5, m[1])
			flip()

		flush()
		message("Press any key to start.", registration=5, location=[P.screen_c[0], P.screen_y * 0.8])
		flip()
		any_key()


	def setup_response_collector(self):
		self.rc.display_callback = self.toj_judgement if self.trial_type == TARGET else self.color_judgement
		self.rc.terminate_after = [10, TK_S]
		if self.trial_type == PROBE:
			self.rc.uses(RC_COLORSELECT)
			self.rc.color_listener.set_wheel(self.wheel)
			self.rc.color_listener.set_target(self.probe)
			self.rc.color_listener.interrupts = True
		else:
			self.rc.uses(RC_KEYPRESS)
			self.rc.keypress_listener.key_map = KeyMap('primary', *self.response_collector_keymapping)
			self.rc.keypress_listener.interrupts = True

	def trial_prep(self):
		self.target_1_loc = self.box_l_pos if self.target_loc == LEFT else self.box_r_pos
		self.target_2_loc = self.box_r_pos if self.target_loc == LEFT else self.box_l_pos
		self.t1 = self.v_line.render() if self.first_target == VERTICAL else self.h_line.render()
		self.t2 = self.h_line.render() if self.first_target == VERTICAL else self.v_line.render()

		self.wheel.rotation = int(random.uniform(0, 360))
		self.probe_angle = int(random.uniform(0, 360))
		self.probe_color = colors[self.probe_angle]
		self.wheel.render()

		self.probe.fill = self.probe_color
		self.probe.render()
		self.probe_loc = self.probe_locs.pop() if self.trial_type == PROBE else NA
		self.probe_pos = self.box_l_pos if self.probe_loc == LEFT else self.box_r_pos

		events = [[self.t1_offset_constant + choice(range(15,450,15)), 'target_1_on']]
		events.append([events[-1][0] + 200, 'probe_off'])  # original 350 ms 
		events.append([events[-2][0] + int(self.soa), 'target_2_on'])
		events.append([events[-1][0] + 300, 'target_2_off'])
		for e in events:
			self.evm.register_ticket(ET(e[1], e[0]))
		if P.trial_number > 1:
			fill()
			blit(self.trial_start_message, registration=5, location=P.screen_c)
			flip()
			any_key()
		fill()

		self.display_refresh(False)

	def trial(self):
		while self.evm.before('target_2_off', True):
			self.display_refresh(False)
			if self.evm.after('target_1_on', False):
				blit(self.t1, location=self.target_1_loc, registration=5)
			if self.evm.after('target_2_on', False):
				blit(self.t2, location=self.target_2_loc, registration=5)
			if self.trial_type == PROBE and self.evm.before('probe_off', False) and self.evm.after('target_1_on', False):
					blit(self.probe, location=self.probe_pos, registration=5)
			flip()
		self.rc.collect()
		fill()
		flip()
		if self.trial_type == PROBE:
			probe_judgement_diff = int(self.probe_angle) - self.rc.color_listener.response(True, False)
		else:
			probe_judgement_diff = NA

		return {
			"block_num": P.block_number,
			"trial_num": P.trial_number,
			"trial_type": self.trial_type,
			"toj_judgement_type": P.toj_judgement,
			"block_bias": self.probe_pos_bias_loc,
			"soa": self.soa,
			"rotation": self.wheel.rotation,
			"probe_initial_bias": P.initial_probe_pos_bias_loc,
			"probe_loc": self.probe_loc if self.trial_type == PROBE else NA,
			"probe_color": self.probe_color if self.trial_type == PROBE else NA,
			"probe_angle": int(self.probe_angle) if self.trial_type == PROBE else NA,
			"probe_judgement": self.rc.color_listener.response(True, False) if self.trial_type == PROBE else NA,
			"probe_judgement_color": colors[int(self.rc.color_listener.response(True, False))]if self.trial_type == PROBE else NA,
			"p_minus_j": probe_judgement_diff,
			"probe_rt": self.rc.color_listener.response(False, True) if self.trial_type == PROBE else NA,
			"t1_loc": self.target_loc,
			"t1_type": self.first_target,
			"toj_judgement": self.rc.keypress_listener.response(True, False) if self.trial_type == TARGET else NA,
			"toj_rt": self.rc.keypress_listener.response(False, True) if self.trial_type == TARGET else NA
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
		blit(self.toj_judgement_m, 5, P.screen_c)
		flip()

	def color_judgement(self):
		fill()
		blit(self.wheel, location=P.screen_c, registration=5)
		blit(self.wheel_disc, 5, P.screen_c)
		blit(self.color_judgement_m, 5, P.screen_c)
		flip()