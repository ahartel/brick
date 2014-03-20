import os,re,subprocess
from waflib import Task,Errors,TaskGen,Configure,Node,Logs
from TclParser import *

def configure(conf):
	"""This function gets called by waf upon loading of this module in a configure method"""

	conf.load('brick_general')

	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'

	# find_program returns os.environ['ENCOUNTER'] which gets defined by
	# module load, but it's wrong, therefore we'll hide it
	stash = os.environ['ENCOUNTER']
	os.environ['ENCOUNTER'] = ''
	conf.find_program('encounter', var='ENCOUNTER')
	os.environ['ENCOUNTER'] = stash

	# encounter options
	conf.env['ENCOUNTER_OPTIONS'] = ['-nowin','-overwrite']

def read_additional_files(input_list):
	return_string = '" '
	for item in input_list:
		return_string += item+' '
	return_string += '"'

	return return_string

@TaskGen.taskgen_method
def get_encounter_step_name(self):
	return Node.split_path(self.get_encounter_main_tcl_script().change_ext('').abspath())[-1]

@TaskGen.feature('encounter')
@TaskGen.before('process_source')
def create_encounter_task(self):
	# get a node object for the main tcl script
	self.main_tcl_script = self.get_encounter_main_tcl_script()

	# store netlist in an environment variable
	#self.netlist = getattr(self,'netlist',self.path)
	# store constraints file in an evironment variable
	#self.constraints = getattr(self,'constraints',self.path)

	# disable the process_source function
	self.source = []

	# create results output directory
	try:
		self.results_dir = self.get_or_create_enc_results_dir()
	except Errors.WafError as e:
		Logs.error(e.msg)
		return 1

	# read additional lef/gds/lib
	self.encounter_additional_lef = read_additional_files(getattr(self,'additional_physical_libraries',[]))
	self.encounter_additional_gds = read_additional_files(getattr(self,'additional_gds_files',[]))
	self.encounter_additional_lib = read_additional_files(getattr(self,'additional_timing_libraries',[]))

	# define input list
	inputs = [self.main_tcl_script]
	if hasattr(self,'netlist'):
		inputs.extend(self.to_nodes(self.netlist))
	if hasattr(self,'constraints'):
		inputs.extend(self.to_nodes(self.constraints))
	if hasattr(self,'previous_state'):
		inputs.extend(self.to_nodes(self.previous_state))

	# define output list
	try:
		outputs = [self.get_encounter_state()]
	except Errors.WafError as e:
		Logs.error(e.msg)
		return 1

	p = TclParser()
	p.input_file(self.main_tcl_script.abspath())
	#for cmd in p.parse():
	#	print cmd
	#	pass

	t = self.create_task('encounterTask', inputs, outputs)

@TaskGen.taskgen_method
def get_encounter_main_tcl_script(self):
	main_tcl_script = None
	try:
		main_tcl_script = self.path.find_node(self.tcl_script)
	except AttributeError:
		Logs.error('You have to specify a the attribute \'tcl_script\' for feature "encounter".')
		return 1
	try:
		main_tcl_script.abspath()
	except AttributeError:
		Logs.error('In encounter: TCL script '+self.tcl_script+' not found.')
		return 1

	return main_tcl_script

@TaskGen.taskgen_method
def get_or_create_enc_results_dir(self):
	if not hasattr(self,'name'):
		raise Errors.WafError('In synopsys_dcshell: Please define the attribute \'name\' for this Task generator.')

	results_dir = self.bld.bldnode.make_node('results_'+self.name)
	results_dir.mkdir()

	if not results_dir.find_dir(self.design_name+'_enc'):
		results_dir.make_node(self.design_name+'_enc').mkdir()

	return results_dir

@TaskGen.taskgen_method
def get_encounter_state(self):
	if not hasattr(self,'design_name'):
		raise Errors.WafError('In synopsys_dcshell: Please define the attribute \'design_name\' for this Task generator.')

	tcl_basename = self.get_encounter_step_name()
	return self.get_or_create_enc_results_dir().find_dir(self.design_name+'_enc').make_node(self.design_name+'_'+tcl_basename+'.enc')

#@Task.always_run
class encounterTask(Task.Task):
	vars = ['ENCOUNTER','ENCOUNTER_OPTIONS']

	def run(self):
		logfile = self.generator.get_logdir_node().make_node(self.generator.name+'_'+self.generator.get_encounter_step_name()+'.log')

		run_str = 'BRICK_RESULTS=%s ENCOUNTER_NETLIST=%s ENCOUNTER_CONSTRAINTS=%s ENCOUNTER_ADDITIONAL_LEF=%s ENCOUNTER_ADDITIONAL_GDS=%s ENCOUNTER_ADDITIONAL_LIB=%s %s %s -init %s -log %s' % (
				self.generator.results_dir.abspath(),
				(self.generator.netlist.abspath() if hasattr(self.generator,'netlist') else '""'),
				(self.generator.constraints.abspath() if hasattr(self.generator,'constraints') else '""'),
				self.generator.encounter_additional_lef,
				self.generator.encounter_additional_gds,
				self.generator.encounter_additional_lib,
				self.env.ENCOUNTER,
				" ".join(self.env.ENCOUNTER_OPTIONS),
				self.generator.main_tcl_script.abspath(),
				logfile.abspath()
			)
		out = ""
		try:
			out = self.generator.bld.cmd_and_log(run_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		except Exception as e:
			#out = e.stdout + e.stderr
			pass

		#f = open(logfile.abspath(),'w')
		#f.write(out)
		#f.close()

		return 0

# vim: noexpandtab:
