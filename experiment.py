import klibs

__author__ = "jon mulle"

from klibs import Params
from random import choice
from klibs.KLDraw import *
from klibs.KLKeyMap import KeyMap
import time
import random
from klibs.KLDraw import colors
from klibs.KLUtilities import *
from klibs.KLConstants import *
from klibs.KLEventInterface import EventTicket as ET

LEFT = "LEFT"
RIGHT = "RIGHT"
PROBE = "PROBE"
TARGET = "TARGET"
WHITE = (255, 255, 255, 255)
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
	probe_bias_freq = 8
	color_list = None
	t1_offset_constant = 1380
	toj_judgement_m = None  # pre-rendered message
	color_judgement_m = None  # ditto
	trial_start_message = None

	# timing
	target_onset = 500  # ms

	# dynamic vars
	probe_color = None
	probe_loc = None  # english string (left/right)
	probe_pos = None  # coordinate tuple
	target_loc = None  # as LEFT or RIGHT, ie. for data
	target_1_loc = None
	target_2_loc = None
	t1 = None
	t2 = None
	wheel = None

	def __init__(self, *args, **kwargs):
		super(TOJ_Extension, self).__init__(*args, **kwargs)

	def setup(self):
		Params.key_maps['TOJ_Extension_response'] = klibs.KeyMap('TOJ_Extension_response', [], [], [])
		self.box_l_pos = (Params.screen_x // 3, Params.screen_c[1])
		self.box_r_pos =  (2 * Params.screen_x // 3, Params.screen_c[1])
		self.h_line = Line(deg_to_px(self.line_len_dv), self.box_border_color, self.box_border_stroke, 90)
		self.v_line = Line(deg_to_px(self.line_len_dv), self.box_border_color, self.box_border_stroke)
		self.probe_pos_bias_loc = LEFT if Params.initial_probe_pos_bias_loc == "RIGHT" else RIGHT  # allows block-level toggling without inverting initial value
		self.box = Rectangle(deg_to_px(self.box_size_dva), stroke=[self.box_border_stroke, self.box_border_color, STROKE_INNER]).render()
		self.fixation = Asterisk(deg_to_px(self.fixation_size_dva), WHITE, 4)
		self.probe_prototype = Circle(20)  # NOT dv in the baseball original, alas
		self.wheel_prototype = ColorWheel(500)
		self.text_manager.add_style('probe_bias', 28, [20, 180, 220, 255])
		self.toj_judgement_m = self.message("Which line appeared first?\n (Vertical = z   Horizontal = /)", blit=False)
		self.color_judgement_m = self.message('Choose a color.', blit=False)
		self.trial_start_message = self.message("Press space to continue", "default", registration=5, location=Params.screen_c, blit=False)

	def block(self, block_num):
		self.probe_neg_bias_loc = self.probe_pos_bias_loc
		self.probe_pos_bias_loc = LEFT if self.probe_pos_bias_loc == RIGHT else RIGHT
		self.clear()
		blocks_remaining_str = "Block {0} of {1}".format(block_num, Params.blocks_per_experiment)
		self.message(blocks_remaining_str, location=[Params.screen_c[0], 50], registration=5)
		locations = [(Params.screen_c[0], (Params.screen_c[1] // 1.1) - 50),
					 (Params.screen_c[0], (Params.screen_c[1] // 1.1)),
					 (Params.screen_c[0], (Params.screen_c[1] // 0.9) - 50),
					 (Params.screen_c[0], (Params.screen_c[1] // 0.9))]
		distribution_strings = ["During the next block of trials, the colored disk will appear more frequently at "
								"the:", "and less likely at the:"]
		self.message(distribution_strings[0], location=locations[0], registration=5) 
		self.message(self.probe_pos_bias_loc, 'probe_bias', location=locations[1], registration=5)
		self.message(distribution_strings[1], location=locations[2], registration=5)
		self.message(self.probe_neg_bias_loc, 'probe_bias', location=locations[3], registration=5)
		self.message("Press any key to start.", location=[Params.screen_c[0], Params.screen_y * 0.8], registration=5, flip=True)
		self.any_key()

	def setup_response_collector(self, trial_factors):
		self.rc.display_callback = self.toj_judgement if trial_factors[1] == TARGET else self.color_judgement
		self.rc.end_collection_event = 'response_period_end'
		self.rc.terminate_after = [10, TK_S]
		self.rc.uses([RC_KEYPRESS, RC_COLORSELECT])
		self.rc.keypress_listener.interrupts = True
		self.rc.color_listener.interrupts = True
		self.rc.color_listener.palette = colors
		self.rc.keypress_listener.key_map = KeyMap('primary', ['KP8', 'KP2'], [VERTICAL, HORIZONTAL], [sdl2.SDLK_KP_8, sdl2.SDLK_KP_2])
		self.rc.disable(RC_KEYPRESS if trial_factors[1] == PROBE else RC_COLORSELECT)
		self.rc.enable(RC_COLORSELECT if trial_factors[1] == PROBE else RC_KEYPRESS)
		r_mapping = self.rc.keypress_listener.key_map	
		response_mapping = "Which line appeared first?\n (Vertical = {0}   Horizontal = {1})".format(*r_mapping.map[0])
		self.toj_response_m = self.message(response_mapping, blit=False)

	def trial_prep(self, trial_factors):
		self.target_1_loc = self.box_l_pos if self.trial_factors[2] == LEFT else self.box_r_pos
		self.target_2_loc = self.box_r_pos if self.trial_factors[2] == LEFT else self.box_l_pos
		self.t1 = self.v_line.render() if trial_factors[3] == VERTICAL else self.h_line.render()
		self.t2 = self.h_line.render() if trial_factors[3] == VERTICAL else self.v_line.render()

		self.wheel_prototype.rotation= random.uniform(0, 360)
		self.wheel = self.wheel_prototype.render()
		self.rc.color_listener.target(self.wheel, Params.screen_c, 5)
		self.probe_color = random.choice(colors)  # saved for data file
		self.probe_prototype.fill = self.probe_color
		self.probe = self.probe_prototype.render()
		self.probe_loc = random.choice([self.probe_pos_bias_loc] * self.probe_bias_freq + [self.probe_neg_bias_loc])
		self.probe_pos = self.box_l_pos if self.probe_loc == LEFT else self.box_r_pos

		events = [[self.t1_offset_constant + choice(range(15,450,15)), 'target_1_on']]
		events.append([events[-1][0] + 350, 'probe_off'])
		events.append([events[-2][0] + int(trial_factors[4]), 'target_2_on'])
		events.append([events[-1][0] + 300, 'target_2_off'])
		for e in events:
			Params.clock.register_event(ET(e[1], e[0]))
		if Params.trial_number > 1:
			self.fill()	
			self.blit(self.trial_start_message, registration=5, location=Params.screen_c)
			self.flip()
			self.any_key()	
		self.fill()
		self.display_refresh(False)

	def trial(self, trial_factors):
		on = None
		while self.evi.before('target_2_off', True):
			self.display_refresh(False)
			if self.evi.after('target_1_on', False):
				self.blit(self.t1, location=self.target_1_loc, registration=5)
			if self.evi.after('target_2_on', False):
				self.blit(self.t2, location=self.target_2_loc, registration=5)
			if trial_factors[1] == PROBE and self.evi.before('probe_off', False) and self.evi.after('target_1_on', False):
					self.blit(self.probe, location=self.probe_loc, registration=5)
			self.flip()
		self.rc.collect()
		self.fill()
		self.flip()
		if trial_factors[1] == PROBE and self.rc.color_listener.response_made():
			probe_index = colors.index(self.probe_color)
			response_index = colors.index(self.rc.color_listener.response(True, False))
			col_diff = probe_index - response_index
			if col_diff < 0:
				col_diff = response_index - probe_index
		else:
			probe_index = -1
			response_index = -1
			col_diff = -1

		return {
			"block_num": Params.block_number,
			"trial_num": Params.trial_number,
			"trial_type": trial_factors[1],
			"soa": trial_factors[4],
			"probe_loc": self.probe_loc,
			"probe_color": self.probe_color if trial_factors[1] == PROBE else NA,
			"probe_color_index": probe_index,
			"probe_judgement": self.rc.color_listener.response(True, False),
			"probe_judgement_index": response_index,
			"probe_index_diff": col_diff,
			"probe_rt": self.rc.color_listener.response(False, True),
			"t1_loc": self.target_loc,
			"t1_type": trial_factors[3],
			"toj_judgement": self.rc.keypress_listener.response(True, False),
			"toj_rt": self.rc.keypress_listener.response(False, True),
		}

	def trial_clean_up(self, trial_id, trial_factors):
		pass

	def clean_up(self):
		pass

	def display_refresh(self, flip=True):
		self.fill()
		self.blit(self.box, location=self.box_l_pos, registration=5)
		self.blit(self.box, location=self.box_r_pos, registration=5)
		self.blit(self.fixation, location=Params.screen_c, registration=5)
		if flip:
			self.flip()

	def toj_judgement(self):
		self.fill()
		self.blit(self.toj_judgement_m, 5, Params.screen_c)
		self.flip()


	def color_judgement(self):
		self.fill()
		self.blit(self.wheel, location=Params.screen_c, registration=5)
		self.blit(self.color_judgement_m, 5, Params.screen_c)
		self.flip()