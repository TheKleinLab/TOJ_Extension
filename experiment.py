import klibs

__author__ = "jon mulle"

from klibs import Params
import time
from random import choice
from klibs.KLDraw import *
from klibs.KLKeyMap import KeyMap
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
	probe_lrg_bias_freq = 8
	probe_sml_bias_freq = 2
	color_list = None
	toj_judgement_m = None  # pre-rendered message
	color_judgement_m = None  # ditto
	trial_start_message = None
	cursor_dot = None

	# timing
	target_onset = 500  # ms
	t1_offset_constant = 1380  # ms

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
	wheel = None

	def __init__(self, *args, **kwargs):
		super(TOJ_Extension, self).__init__(*args, **kwargs)

	def setup(self):
		hide_mouse_cursor()
		self.clear()
		self.cursor_dot = Circle(5, fill=[0,0,0], stroke=[1,[255,2555,255]]).render()
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
		self.text_manager.add_style('small', 14, [255, 255, 255, 255])
		self.color_judgement_m = self.message('Choose a color.', blit=False)
		self.trial_start_message = self.message("Press space to continue", "default", registration=5, location=Params.screen_c, blit=False)
		self.insert_practice_block((1,2,4), trial_counts = 40, factor_masks=[
								   [[0,1,0,0,0],[1,1,1,1,1],[1,1,1,1,1],[1,1,1,1,1]],
								   [[1,0,0,0,0],[1,1,1,1,1],[1,1,1,1,1],[1,1,1,1,1]],
								   [[1,0,0,0,0],[1,1,1,1,1],[1,1,1,1,1],[1,1,1,1,1]]])

	def block(self):
		self.fill()
		# make sure there are enough of these to finish the block AND that this doesn't apply during practice blocks
		self.probe_locs = [[self.probe_pos_bias_loc] * self.probe_lrg_bias_freq + [self.probe_neg_bias_loc] * self.probe_sml_bias_freq]
		if Params.block_number in (3,5):
			self.probe_locs *= 24
		random.shuffle(self.probe_locs)
		def_size = self.text_manager.styles['default'].font_size_px
		bias_size =self.text_manager.styles['probe_bias'].font_size_px
		msg_y = 50
		blocks_remaining_str = "Block {0} of {1}".format(Params.block_number, Params.blocks_per_experiment)
		self.message(blocks_remaining_str, 'default', registration=5, location=[Params.screen_c[0], msg_y])
		msg_y += 2 * def_size
		if Params.practicing:
			self.message("(This is a practice block.)", 'default', registration=5, location=[Params.screen_c[0], msg_y])
		msg_y = int(Params.screen_c[1] - 0.5* (5 * def_size + bias_size))
		if Params.block_number != 1:
			if Params.block_number not in (3,5): # immediately after each probe-trial practice, repeat probe bias
				self.probe_neg_bias_loc = self.probe_pos_bias_loc
				self.probe_pos_bias_loc = LEFT if self.probe_pos_bias_loc == RIGHT else RIGHT

			probe_strings = ["During this block, the colored disk will appear more often on the:", "and less often on the:"]
			self.message(probe_strings[0], location=[Params.screen_c[0], msg_y], registration=5)
			msg_y += 2 * def_size
			self.message(self.probe_pos_bias_loc, 'probe_bias', registration=5, location=[Params.screen_c[0], msg_y])
			msg_y += def_size + bias_size
			self.message(probe_strings[1], 'default', registration=5, location=[Params.screen_c[0], msg_y])
			msg_y += 2 * def_size
			self.message(self.probe_neg_bias_loc, 'probe_bias', registration=5, location=[Params.screen_c[0], msg_y])
			# msg_y =+ def_size + bias_size
		self.message("Press any key to start.", registration=5, location=[Params.screen_c[0], Params.screen_y * 0.8], flip=True)
		self.any_key()

	def setup_response_collector(self):
		self.rc.display_callback = self.toj_judgement if self.trial_type == TARGET else self.color_judgement
		self.rc.end_collection_event = 'response_period_end'
		self.rc.terminate_after = [10, TK_S]
		self.rc.uses([RC_KEYPRESS, RC_COLORSELECT])
		self.rc.keypress_listener.interrupts = True
		self.rc.color_listener.interrupts = True
		anulus_inner_bound = self.wheel_prototype.radius - self.wheel_prototype.thickness
		self.rc.color_listener.add_boundary("color_ring", [Params.screen_c, anulus_inner_bound, self.wheel_prototype.radius], "anulus")
		self.rc.keypress_listener.key_map = KeyMap('primary', ['Key Pad 8', 'Key Pad 2'], [VERTICAL, HORIZONTAL], [sdl2.SDLK_KP_8, sdl2.SDLK_KP_2])
		self.rc.disable(RC_KEYPRESS if self.trial_type == PROBE else RC_COLORSELECT)
		self.rc.enable(RC_COLORSELECT if self.trial_type == PROBE else RC_KEYPRESS)
		r_mapping = self.rc.keypress_listener.key_map
		rmap_values = r_mapping.map[0]
		rmap_values.append(Params.toj_judgement)
		response_mapping = "Which line appeared {2}?\n (Vertical = {0}   Horizontal = {1})".format(*rmap_values )
		self.toj_judgement_m = self.message(response_mapping, blit=False)
		self.rc.color_listener.set_target(self.wheel_prototype, Params.screen_c, 5)

	def trial_prep(self):
		self.target_1_loc = self.box_l_pos if self.target_loc == LEFT else self.box_r_pos
		self.target_2_loc = self.box_r_pos if self.target_loc == LEFT else self.box_l_pos
		self.t1 = self.v_line.render() if self.first_target == VERTICAL else self.h_line.render()
		self.t2 = self.h_line.render() if self.first_target == VERTICAL else self.v_line.render()

		self.wheel_prototype.rotation = int(random.uniform(0, 360))
		self.probe_angle = int(random.uniform(0, 360))
		self.probe_color = colors[self.probe_angle]
		self.wheel = self.wheel_prototype.render()

		self.probe_prototype.fill = self.probe_color
		self.probe = self.probe_prototype.render()
		self.probe_loc = self.prob_locs.pop()
		self.probe_pos = self.box_l_pos if self.probe_loc == LEFT else self.box_r_pos

		events = [[self.t1_offset_constant + choice(range(15,450,15)), 'target_1_on']]
		events.append([events[-1][0] + 200, 'probe_off'])  # original 350 ms 
		events.append([events[-2][0] + int(self.soa), 'target_2_on'])
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

	def trial(self):
		while self.evi.before('target_2_off', True):
			self.display_refresh(False)
			if self.evi.after('target_1_on', False):
				self.blit(self.t1, location=self.target_1_loc, registration=5)
			if self.evi.after('target_2_on', False):
				self.blit(self.t2, location=self.target_2_loc, registration=5)
			if self.trial_type == PROBE and self.evi.before('probe_off', False) and self.evi.after('target_1_on', False):
					self.blit(self.probe, location=self.probe_pos, registration=5)
			self.flip()
		self.rc.collect()
		self.fill()
		self.flip()
		if self.trial_type == PROBE:
			probe_judgement_diff = int(self.probe_angle) - self.rc.color_listener.response(True, False)
		else:
			probe_judgement_diff = NA

		return {
			"block_num": Params.block_number,
			"trial_num": Params.trial_number,
			"trial_type": self.trial_type,
			"toj_judgement_type": Params.toj_judgement,
			"soa": self.soa,
			"rotation": self.wheel_prototype.rotation,
			"probe_initial_bias": Params.initial_probe_pos_bias_loc,
			"probe_loc": self.probe_loc if self.trial_type == PROBE else NA,
			"probe_color": self.probe_color if self.trial_type == PROBE else NA,
			"probe_angle": int(self.probe_angle) if self.trial_type == PROBE else NA,
			"probe_judgement": self.rc.color_listener.response(True, False) if self.trial_type == PROBE else NA,
			"probe_judgement_color": colors[int(self.rc.color_listener.response(True, False))]if self.trial_type == PROBE else NA,
			"p_minus_j": probe_judgement_diff,
			"probe_rt": self.rc.color_listener.response(False, True) if self.trial_type == PROBE else NA,
			"t1_loc": self.target_loc,
			"t1_type": self.first_target,
			"toj_judgement": self.rc.keypress_listener.response(True, False),
			"toj_rt": self.rc.keypress_listener.response(False, True)
		}

	def trial_clean_up(self):
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
		show_mouse_cursor()
		self.fill()
		self.blit(self.wheel, location=Params.screen_c, registration=5)
		self.blit(self.color_judgement_m, 5, Params.screen_c)
		self.flip()
		hide_mouse_cursor()