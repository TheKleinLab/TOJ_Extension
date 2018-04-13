from klibs.KLIndependentVariable import IndependentVariableSet, IndependentVariable


# Initialize object containing project's independent variables

TOJ_Extension_ind_vars = IndependentVariableSet()


# Define project variables and variable types

## Factors ##
# 'trial_type': the type of trial ("PROBE" = colour probe, "TARGET" = TOJ)
# 'target_loc': the location of the first target to appear during the trial
# 'first_target': the orientation of the line (vertical or horizontal) that appears first
# 'soa': the interval between the onsets of the first and second targets

flip = 1000/60.0 # Time required per refresh of the screen
soa_list = [(flip, 3), (flip*3, 2), (flip*6, 2), (flip*9, 2), (flip*16, 1)]

TOJ_Extension_ind_vars.add_variable("trial_type", str, ["PROBE", ("TARGET", 2)])
TOJ_Extension_ind_vars.add_variable("target_loc", str, ["LEFT", "RIGHT"])
TOJ_Extension_ind_vars.add_variable("first_target", str, ["vertical", "horizontal"])
TOJ_Extension_ind_vars.add_variable("soa", float, soa_list)
