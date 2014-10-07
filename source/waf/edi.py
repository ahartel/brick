import os,re,subprocess
from waflib import Task,Errors,TaskGen,Configure,Node,Logs
from TclParser import *
from brick_general import ChattyBrickTask

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
	conf.env['ENCOUNTER_OPTIONS'] = ['-nowin','-overwrite','-exitOnError']

@TaskGen.taskgen_method
def read_additional_enc_files(self,attr):
	input_list = getattr(self,attr,[])
	return_string = '" '
	for item in input_list:
		try:
			return_string += self.path.find_node(item).abspath()+' '
		except AttributeError:
			self.bld.fatal("edi.py: "+attr+" "+item+" not found.")

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

	self.do_run = getattr(self,'do_run',True)

	# disable the process_source function
	self.source = []

	# create results output directory
	try:
		self.results_dir = self.get_or_create_enc_results_dir()
	except Errors.WafError as e:
		Logs.error(e.msg)
		return 1

	# read additional lef/gds/lib
	self.encounter_additional_lef = self.read_additional_enc_files('additional_physical_libraries')
	self.encounter_additional_gds = self.read_additional_enc_files('additional_gds_files')
	self.encounter_additional_lib = self.read_additional_enc_files('additional_timing_libraries')

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

	if self.do_run:
		t = self.create_task('encounterTask', inputs, outputs)


@TaskGen.taskgen_method
def get_encounter_logfile_node(self):
	return self.get_logdir_node().make_node(self.design_name+'_'+self.get_encounter_step_name()+'.log')

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
		raise Errors.WafError('In edi: Please define the attribute \'name\' for this Task generator.')

	results_dir = self.bld.bldnode.make_node('results_'+self.design_name)
	results_dir.mkdir()

	if not results_dir.find_dir(self.design_name+'_enc'):
		results_dir.make_node(self.design_name+'_enc').mkdir()

	return results_dir

@TaskGen.taskgen_method
def get_encounter_state(self):
	if not hasattr(self,'design_name'):
		raise Errors.WafError('In edi: Please define the attribute \'design_name\' for this Task generator.')

	tcl_basename = self.get_encounter_step_name()
	return self.get_or_create_enc_results_dir().find_dir(self.design_name+'_enc').make_node(self.design_name+'_'+tcl_basename+'.enc')

@TaskGen.taskgen_method
def get_encounter_environment_string(self):
	ret_string = ''
	if hasattr(self,'netlist'):
		ret_string += ' ENCOUNTER_NETLIST='+self.netlist.abspath()
	if hasattr(self,'constraints'):
		ret_string += ' ENCOUNTER_CONSTRAINTS='+self.constraints.abspath()
	if hasattr(self,'encounter_additional_lef'):
		ret_string += ' ENCOUNTER_ADDITIONAL_LEF='+self.encounter_additional_lef
	if hasattr(self,'encounter_additional_gds'):
		ret_string += ' ENCOUNTER_ADDITIONAL_GDS='+self.encounter_additional_gds
	if hasattr(self,'encounter_additional_lib'):
		ret_string += ' ENCOUNTER_ADDITIONAL_LIB='+self.encounter_additional_lib
	return ret_string

@TaskGen.taskgen_method
def get_encounter_flat_options(self):
	return " ".join(self.env.ENCOUNTER_OPTIONS)

@Task.always_run
class encounterTask(ChattyBrickTask):
	vars = ['ENCOUNTER','ENCOUNTER_OPTIONS']
	shell = True
	run_str = 'BRICK_RESULTS=${gen.results_dir.abspath()} ${gen.get_encounter_environment_string()} ${env.ENCOUNTER} ${gen.get_encounter_flat_options()} -init ${gen.main_tcl_script.abspath()} -log ${gen.get_encounter_logfile_node().abspath()}'

	def check_output(self,ret,out):
		for num,line in enumerate(out.split('\n')):
			if line.find('**ERROR:') == 0:
				Logs.error("Error in line %d: %s" % (num,line[8:]))
				ret = 1

		return ret


# vim: noexpandtab:
