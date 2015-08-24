import os,re,subprocess,logging
from waflib import Task,Errors,TaskGen,Configure,Node,Logs
from TclParser import EncounterTclParser
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
def read_additional_enc_files(self,attr,key=None):
	return_string = ''

	if key is None:
		input_list = getattr(self,attr,[])
		for item in input_list:
			return_string += self.path.make_node(item).abspath()+' '
	else:
		input_dict = getattr(self,attr,{})
		if key in input_dict:
			for item in input_dict[key]:
				return_string += self.path.make_node(item).abspath()+' '

	if len(return_string) > 0:
		return '" '+return_string+' "'
	else:
		return '""'

@TaskGen.taskgen_method
def get_encounter_step_name(self):
	return Node.split_path(self.get_encounter_main_tcl_script().change_ext('').abspath())[-1]

@TaskGen.feature('encounter')
@TaskGen.before('process_source')
def create_encounter_task(self):
	# get a node object for the main tcl script
	self.main_tcl_script = self.get_encounter_main_tcl_script()
	brick_tcl_script = self.bld.bldnode.make_node('brick_'+os.path.basename(self.main_tcl_script.abspath()))

	self.do_run = getattr(self,'do_run',True)

	# disable the process_source function
	self.source = []

	# create results output directory
	try:
		self.results_dir = self.get_or_create_enc_results_dir()
	except Errors.WafError as e:
		Logs.error(e.msg)
		return 1

	# define input list
	inputs = [self.main_tcl_script]
	if hasattr(self,'previous_state'):
		inputs.extend(self.to_nodes(self.previous_state))

	# read additional lef/gds/lib
	with open(brick_tcl_script.abspath(),'w') as fh:
		self.write_encounter_tcl_variable(fh,'BRICK_RESULTS',self.results_dir.path_from(self.bld.bldnode))

		encounter_additional_lef = self.read_additional_enc_files('additional_physical_libraries')
		self.write_encounter_tcl_variable(fh,'ENCOUNTER_ADDITIONAL_LEF',encounter_additional_lef)
		encounter_additional_gds = self.read_additional_enc_files('additional_gds_files')
		self.write_encounter_tcl_variable(fh,'ENCOUNTER_ADDITIONAL_GDS',encounter_additional_gds)

		encounter_additional_lib_typ = self.read_additional_enc_files('additional_timing_libraries',
																	  'typ')
		self.write_encounter_tcl_variable(fh,
										  'ENCOUNTER_ADDITIONAL_LIB_TYP',
										  encounter_additional_lib_typ)

		encounter_additional_lib_min = self.read_additional_enc_files('additional_timing_libraries',
																	  'min')
		self.write_encounter_tcl_variable(fh,
										  'ENCOUNTER_ADDITIONAL_LIB_MIN',
										  encounter_additional_lib_min)

		encounter_additional_lib_max = self.read_additional_enc_files('additional_timing_libraries',
																	  'max')
		self.write_encounter_tcl_variable(fh,
										  'ENCOUNTER_ADDITIONAL_LIB_MAX',
										  encounter_additional_lib_max)

		if hasattr(self,'netlist'):
			netlist = self.to_nodes(self.netlist)
			inputs.extend(netlist)
			netlist_string = " ".join([c.abspath() for c in netlist])
			self.write_encounter_tcl_variable(fh,'ENCOUNTER_NETLIST','"'+netlist_string+'"')
		else:
			self.write_encounter_tcl_variable(fh,'ENCOUNTER_NETLIST','""')
		if hasattr(self,'constraints'):
			constraints = self.to_nodes(self.constraints)
			print constraints
			inputs.extend(constraints)
			constraints_string = " ".join([c.abspath() for c in constraints])
			self.write_encounter_tcl_variable(fh,'ENCOUNTER_CONSTRAINTS','"'+constraints_string+'"')
		else:
			self.write_encounter_tcl_variable(fh,'ENCOUNTER_CONSTRAINTS','""')

	# declare output list
	outputs = []
	try:
		outputs.append(self.get_encounter_state())
	except Errors.WafError as e:
		Logs.error(e.msg)

	#p = TclParser()
	#p.input_file(self.main_tcl_script.abspath())
	#for cmd in p.parse():
	#	if cmd[0] == 'streamOut':
	#		pass
	#	if cmd[0] == 'saveDesign':
	#		try:
	#			outputs.append(self.get_encounter_state())
	#		except Errors.WafError as e:
	#			Logs.error(e.msg)
	#			return 1
	#		break

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
def write_encounter_tcl_variable(self,filehandle,name,value):
	assert isinstance(value,basestring)
	filehandle.write('set '+name+' '+value+'\n')

@TaskGen.taskgen_method
def get_encounter_flat_options(self):
	return " ".join(self.env.ENCOUNTER_OPTIONS)

@Task.always_run
class encounterTask(ChattyBrickTask):
	vars = ['ENCOUNTER','ENCOUNTER_OPTIONS']
	shell = True
	run_str = '${env.ENCOUNTER} ${gen.get_encounter_flat_options()} -init ${gen.main_tcl_script.abspath()} -log ${gen.get_encounter_logfile_node().abspath()}'

	def check_output(self,ret,out):
		for num,line in enumerate(out.split('\n')):
			if line.find('**ERROR:') == 0:
				Logs.error("Error in line %d: %s" % (num,line[8:]))
				ret = 1

		return ret


# vim: noexpandtab:
