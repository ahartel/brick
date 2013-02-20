import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs

def configure(conf):
	"""This function gets called by waf upon loading of this module in a configure method"""

	conf.load('brick_general')

	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'
	conf.env['ALTOS_LIBERATE'] = 'liberate'
	conf.env['ALTOS_LIBERATE_MX'] = 'liberate_mx'
	conf.env['ALTOS_LIBERATE_OPTIONS'] = [
		]


@TaskGen.feature('altos_liberate')
def create_altos_lib_task(self):

	self.liberate_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'liberate_script_'+self.cell+'.tcl'))

	if not getattr(self,'netlists_spice',None):
		self.netlists_spice = []
	if not getattr(self,'netlists_spectre',None):
		self.netlists_spectre = []

	netlists_strings_spice = []
	for netlist in getattr(self,'netlists_spice',[]):
		#if not netlist:
		#	Logs.error('You have given an undefined node object as netlist for feature "altos_liberate".')
		#	return
		try:
			netlists_strings_spice.append(netlist.abspath())
		except AttributeError:
			netlists_strings_spice.append(netlist)

	netlists_strings_spectre = []
	for netlist in getattr(self,'netlists_spectre',[]):
		#if not netlist:
		#	Logs.error('You have given an undefined node object as netlist for feature "altos_liberate".')
		#	return
		try:
			netlists_strings_spectre.append(netlist.abspath())
		except AttributeError:
			netlists_strings_spectre.append(netlist)


	output_library = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,self.cell+'.lib'))

	f = open(self.liberate_script.abspath(),"w")
	try:
		tcl_string = """
# Define templates for characterization.
# Delay template for 3 input slews and 3 loads
define_template -type constraint \\
    -index_1 {{0.0001 0.0002 0.0003}} \\
    -index_2 {{0.0001 0.0002 0.0003}} \\
    constraint_3x3

define_template -type delay \\
    -index_1 {{0.026973 0.047707 0.103269 0.334201 0.800188 1.965635}} \\
    -index_2 {{0.002000 0.006100 0.018607 0.056753 0.173106 0.528000}} \\
    delay_6x6

define_template -type delay \\
    -index_1 {{0.0001 0.0002 0.0003 0.0004 0.0005 0.0006 0.0007}} \\
    -index_2 {{0.0001 0.0002 0.0003 0.0004 0.0005 0.0006 0.0007}} \\
    delay_7x7_0

# Power template for 3 input slews and 3 loads
define_template -type power \\
    -index_1 {{0.026968 0.047707 0.103268 0.334201 0.800117 1.965723}} \\
    -index_2 {{0.002000 0.006100 0.018607 0.056753 0.173106 0.528000}} \\
    power_6x6

define_template -type power \\
    -index_1 {{0.0001 0.0002 0.0003 0.0004 0.0005 0.0006 0.0007}} \\
    -index_2 {{0.0001 0.0002 0.0003 0.0004 0.0005 0.0006 0.0007}} \\
    power_7x7_0

# Specify the PVT for this characterization run
set_operating_condition -voltage 1.2 -temp 25

#set_var measure_slew_lower_fall 0.1
#set_var measure_slew_upper_fall 0.9
#set_var measure_slew_lower_rise 0.1
#set_var measure_slew_upper_rise 0.9
#
#set_units -leakage_power 1pw
""".format()
		if netlists_strings_spice:
			tcl_string += """
read_spice -format hspice {{ \\
	{0} \\
}}
""".format(' \\\n\t'.join(netlists_strings_spice))
		if netlists_strings_spectre:
			tcl_string += """
read_spice -format spectre {{ \\
	{0} \\
}}
""".format(' \\\n\t'.join(netlists_strings_spectre))
		tcl_string += """
set_vdd vdd 1.2
set_vdd vdd12a 1.2
set_vdd vdd12d 1.2
set_gnd gnd 0
set_gnd gndd 0
set_gnd gnda 0

define_cell \\
    -input {{ {0} }} \\
    -output {{ {1} }} \\
    -clock {{ {2} }} \\
    -bidi {{ {3} }} \\
    -delay delay_7x7_0 \\
    -power power_7x7_0 \\
    -constraint constraint_3x3 \\
	-pinlist {{ {0} {1} {2} {3} }} \\
    {{ {4} }}

""".format(
				' '.join(getattr(self,'input',[])),
				" ".join(getattr(self,'output',[])),
				" ".join(getattr(self,'clock',[])),
				" ".join(getattr(self,'bidi',[])),
				self.cell,
			)
	except AttributeError:
		Logs.error('Please define a cell name with parameter "cell" for feature "altos_liberate".')

	if hasattr(self,'arcs'):
		tcl_string += " \n".join(self.arcs)
		tcl_string += "\n"

	tcl_string += "char_library -skip {leakage power mpw delay}"
	if hasattr(self,'io_only') and getattr(self,'io_only',False) == True:
		tcl_string += ' -io'
	if hasattr(self,'user_arcs_only') and getattr(self,'user_arcs_only',False) == True:
		tcl_string += ' -user_arcs_only'

	tcl_string += "\nwrite_library -overwrite {0}\n".format(output_library.abspath())

	f.write(tcl_string)
	f.close()

	t = self.create_task('altosLibTask', self.netlists_spice+self.netlists_spectre, output_library)

class altosLibTask(Task.Task):
	vars = ['ALTOS_LIBERATE','ALTOS_LIBERATE_OPTIONS']

	def run(self):
		run_str = '%s %s %s 2>&1' % (self.env.ALTOS_LIBERATE, " ".join(self.env.ALTOS_LIBERATE_OPTIONS), self.generator.liberate_script.abspath())
		out = ""
		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout

		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'altos_liberate_'+self.generator.cell+'.log'))
		f = open(logfile.abspath(),'w')
		f.write(out)
		f.close()

		return 0


@TaskGen.feature('altos_liberate_mx')
def create_altos_lib_mx_task(self):

	self.liberate_script = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'liberate_script_'+self.cell+'.tcl'))

	if not getattr(self,'netlists_spice',None):
		self.netlists_spice = []
	if not getattr(self,'netlists_spectre',None):
		self.netlists_spectre = []

	netlists_strings_spice = []
	for netlist in getattr(self,'netlists_spice',[]):
		#if not netlist:
		#	Logs.error('You have given an undefined node object as netlist for feature "altos_liberate".')
		#	return
		try:
			netlists_strings_spice.append(netlist.abspath())
		except AttributeError:
			netlists_strings_spice.append(netlist)

	netlists_strings_spectre = []
	for netlist in getattr(self,'netlists_spectre',[]):
		#if not netlist:
		#	Logs.error('You have given an undefined node object as netlist for feature "altos_liberate".')
		#	return
		try:
			netlists_strings_spectre.append(netlist.abspath())
		except AttributeError:
			netlists_strings_spectre.append(netlist)


	output_library = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS,self.cell+'.lib'))

	f = open(self.liberate_script.abspath(),"w")
	try:
		tcl_string = """
set vdd 1.2
set gnd 0.0
set temp 25

set_gnd gnd $gnd
set_gnd gndd $gnd
set_vdd vdd $vdd
set_vdd vdd12d $vdd

set_var mx_find_memcores 0
set_var mx_force_constraint_comb_off_if_noarray_found 0

# Specify the PVT for this characterization run
set_operating_condition -voltage $vdd -temp $temp

# Define templates for characterization.
# Delay template for 3 input slews and 3 loads
define_template -type constraint \\
    -index_1 {{0.0001 0.0002 0.0003}} \\
    -index_2 {{0.0001 0.0002 0.0003}} \\
    constraint_3x3

define_template -type delay \\
    -index_1 {{0.026973 0.047707 0.103269 0.334201 0.800188 1.965635}} \\
    -index_2 {{0.002000 0.006100 0.018607 0.056753 0.173106 0.528000}} \\
    delay_6x6

define_template -type delay \\
    -index_1 {{0.0001 0.0002 0.0003 0.0004 0.0005 0.0006 0.0007}} \\
    -index_2 {{0.0001 0.0002 0.0003 0.0004 0.0005 0.0006 0.0007}} \\
    delay_7x7_0

# Power template for 3 input slews and 3 loads
define_template -type power \\
    -index_1 {{0.026968 0.047707 0.103268 0.334201 0.800117 1.965723}} \\
    -index_2 {{0.002000 0.006100 0.018607 0.056753 0.173106 0.528000}} \\
    power_6x6

define_template -type power \\
    -index_1 {{0.0001 0.0002 0.0003 0.0004 0.0005 0.0006 0.0007}} \\
    -index_2 {{0.0001 0.0002 0.0003 0.0004 0.0005 0.0006 0.0007}} \\
    power_7x7_0

set delay_template "delay_7x7_0"
set constraint_template "constraint_3x3"
set power_template "power_7x7_0"

set_var mx_corecell "dual_port"

""".format()

		if hasattr(self,'mxtables'):
			tcl_string += """
set mxtables {{ {0} }}

""".format(" ".join(getattr(self,'mxtables',[])))

		if netlists_strings_spectre:
			tcl_string += """
read_spice -format spectre {{ \\
	{0} \\
}}
""".format(' \\\n\t'.join(netlists_strings_spectre))
		if netlists_strings_spice:
			tcl_string += """
read_spice -format hspice {{ \\
	{0} \\
}}
""".format(' \\\n\t'.join(netlists_strings_spice))

		tcl_string += """

define_cell \\
    -input {{ {0} }} \\
    -output {{ {1} }} \\
    -clock {{ {2} }} \\
    -bidi {{ {3} }} \\
    -delay $delay_template \\
    -power $power_template \\
    -constraint $constraint_template \\
	-pinlist {{ {0} {1} {2} {3} }} \\
""".format(
				' '.join(getattr(self,'input',[])),
				" ".join(getattr(self,'output',[])),
				" ".join(getattr(self,'clock',[])),
				" ".join(getattr(self,'bidi',[]))
		)

		if hasattr(self,'mxtables'):
			tcl_string += "-mxtable $mxtables \\\n"

		tcl_string += "{{ {0} }}\n".format(self.cell)

		tcl_string += """
# setup partition simulator
#set partition_simulator "spectre"
#set partition_simulator "ultrasim"
set partition_simulator "hsim"
mx_set_hsim_param [list \\
    [list hsimspeed 4] \\
    [list hsimvdd $vdd] \\
    [list hsimalloweddv [expr $vdd / 10]] \\
    [list hsimpostl -1] \\
    ]

# set characterization simulator
# if none specified, internal alspice used
set characterization_simulator "ultrasim"
#set characterization_simulator "hspice"
#set characterization_simulator "eldo"
#set characterization_simulator "spectre"

# specify models the memory should be characterized for
# partition (with fast spice) and characterize (with real spice)
#set models []
set models [list -ccs -ccsn -ecsm -ecsmn]
char_macro \\
    -extsim $partition_simulator \\
    -char_params [concat $models -extsim $characterization_simulator]
# write models
#write_library -overwrite {0}{1}
foreach model $models {{
    write_library -overwrite $model {0}$model{1}
}}
""".format(output_library.change_ext("").abspath(),output_library.suffix())
	except AttributeError:
		Logs.error('Please define a cell name with parameter "cell" for feature "altos_liberate".')


	f.write(tcl_string)
	f.close()

	t = self.create_task('altosLibMXTask', self.netlists_spice+self.netlists_spectre, output_library)


@Task.always_run
class altosLibMXTask(Task.Task):
	vars = ['ALTOS_LIBERATE_MX','ALTOS_LIBERATE_OPTIONS']

	def run(self):
		run_str = '%s %s %s 2>&1' % (self.env.ALTOS_LIBERATE_MX, " ".join(self.env.ALTOS_LIBERATE_OPTIONS), self.generator.liberate_script.abspath())
		out = ""
		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout

		logfile = self.generator.path.get_bld().make_node(os.path.join(self.generator.path.bld_dir(),self.env.BRICK_LOGFILES,'altos_liberate_'+self.generator.cell+'.log'))
		f = open(logfile.abspath(),'w')
		f.write(out)
		f.close()

		return 0

# vim: noexpandtab:
