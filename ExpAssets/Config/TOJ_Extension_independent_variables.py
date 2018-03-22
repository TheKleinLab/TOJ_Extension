from klibs.KLIndependentVariable import IndependentVariableSet, IndependentVariable


# Initialize object containing project's independent variables

TOJ_Extension_ind_vars = IndependentVariableSet()


# Define project variables and variable types

soa_list = [(15, 3), (45, 2), (90, 2), (135, 2), (240, 1)]

TOJ_Extension_ind_vars.add_variable("trial_type", str, ["PROBE", ("TARGET", 2)])
TOJ_Extension_ind_vars.add_variable("target_loc", str, ["LEFT", "RIGHT"])
TOJ_Extension_ind_vars.add_variable("first_target", str, ["vertical", "horizontal"])
TOJ_Extension_ind_vars.add_variable("soa", int, soa_list)
