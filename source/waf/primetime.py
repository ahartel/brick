import os,re,subprocess
from waflib import Task,Errors,TaskGen,Configure,Node,Logs
from brick_general import ChattyBrickTask
from TclParser import *

def configure(conf):
	"""This function gets called by waf upon loading of this module in a configure method"""

	conf.load('brick_general')

	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'

	conf.find_program('pt_shell', var='SYNOPSYS_PTSHELL')
	conf.env['SYNOPSYS_PTSHELL_OPTIONS'] = [
		]

@TaskGen.taskgen_method
def get_or_create_pt_results_dir(self):
	if not hasattr(self,'name'):
		raise Errors.WafError('In primetime: Please define the attribute \'name\' for this Task generator.')

	results_dir = self.bld.bldnode.make_node('results_'+self.name)
	results_dir.mkdir()

	return results_dir

@TaskGen.feature('primetime')
@TaskGen.before('process_source')
def create_synopsys_primetime_task(self):
	# get a node object for the main tcl script
	try:
		self.main_tcl_script = self.path.find_node(self.tcl_script)
	except AttributeError:
		Logs.error('You have to specify a the attribute \'tcl_script\' for feature "primetime".')
		return 1
	try:
		self.main_tcl_script.abspath()
	except AttributeError:
		Logs.error('In primetime: TCL script '+self.tcl_script+' not found.')
		return 1

	# convert source list to nodes
	self.sourcelist = self.to_nodes(getattr(self, 'source', []))
	# disable the process_source function
	self.source = []

	# create results output directory
	try:
		self.results_dir = self.get_or_create_pt_results_dir()
	except Errors.WafError as e:
		Logs.error(e.msg)
		return 1

	# generate the node object for the sourcelist TCL script
	# this TCL script contains the commands to actually load the source files into dc_shell
	self.sourcelist_tcl_script = self.path.find_or_declare(self.name+'_source.tcl')

	if not getattr(self,'verilog_sources',None):
		self.verilog_sources = []
	if not getattr(self,'db_sources',None):
		self.db_sources = []
	if not getattr(self,'other_sources',None):
		self.other_sources = []

	# divide sources into groups
	for f in self.sourcelist:
		fn = self.to_nodes(f)[0]

		if fn.suffix() == '.v' or fn.suffix() == '.v':
			self.verilog_sources.append(fn)
		elif fn.suffix() == '.db':
			self.db_sources.append(fn)
		else:
			self.other_sources.append(fn)

	if len(self.other_sources) > 0:
		Logs.error('In primetime: There are unknown source files (at least there extensions indicate that).')
		for file in self.other_sources:
			Logs.error('\t'+file)
		return 1

	# write read statements for every source file into the source list TCL script
	with open(self.sourcelist_tcl_script.abspath(),"w") as f:
		for sourcefile in self.verilog_sources:
			f.write('read_verilog '+sourcefile.abspath()+'\n')
		for sourcefile in self.db_sources:
			f.write('read_db '+sourcefile.abspath()+'\n')

	# parasitics and constraints
	if not hasattr(self,'parasitics'):
		Logs.error('In primetime: Please specify a spef file via parameter \'parasitics\'.')
		return 1
	else:
		self.speffile = self.path.find_node(self.parasitics)

	if not hasattr(self,'constraints'):
		Logs.error('In primetime: Please specify an sdc file via parameter \'constraints\'.')
		return 1
	else:
		self.sdcfile = self.path.find_node(self.constraints)

	# declare input list
	inputs = [self.main_tcl_script]
	inputs.extend(self.db_sources)
	inputs.extend(self.verilog_sources)

	try:
		outputs = []#self.get_synthesized_netlist_node(),self.get_synthesized_constraints_node()]
	except Errors.WafError as e:
		Logs.error(e.msg)
		return 1

	#p = TclParser()
	#p.input_file(self.main_tcl_script.abspath())
	#for cmd in p.parse():
	#	print cmd
	#	pass

	t = self.create_task('synopsysPrimetimeTask', inputs, outputs)

@TaskGen.taskgen_method
def get_synopsys_ptshell_logfile(self):
	return self.get_logdir_node().make_node('pt_shell_'+self.name+'.log')


@Task.always_run
class synopsysPrimetimeTask(ChattyBrickTask):
	vars = ['SYNOPSYS_PTSHELL','SYNOPSYS_PTSHELL_OPTIONS']
	shell = True
	run_str = 'BRICK_RESULTS=${gen.results_dir.abspath()} PTSHELL_SOURCE_TCL=${gen.sourcelist_tcl_script.abspath()} SDCFILE=${gen.sdcfile.abspath()} SPEFFILE=${gen.speffile.abspath()} ${SYNOPSYS_PTSHELL} ${SYNOPSYS_PTSHELL_OPTIONS} -f ${gen.main_tcl_script.abspath()} | tee ${gen.get_synopsys_ptshell_logfile().abspath()}'

	def check_output(self,ret,out):
		for num,line in enumerate(out.split('\n')):
			if line.find('Error:') == 0:
				Logs.error("Error in line %d: %s" % (num,line[6:]))
				ret = 1
			elif line.find('Warning: Unable to resolve reference') == 0:
				Logs.error("Error in line %d: %s" % (num,line[8:]))
				ret = 1

		return ret


# vim: noet:
