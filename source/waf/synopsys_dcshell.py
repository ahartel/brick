import os,re,subprocess
from waflib import Task,Errors,TaskGen,Configure,Node,Logs
from TclParser import *

def configure(conf):
	"""This function gets called by waf upon loading of this module in a configure method"""

	conf.load('brick_general')

	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'

	conf.find_program('dc_shell', var='SYNOPSYS_DCSHELL')
	conf.env['SYNOPSYS_DCSHELL_OPTIONS'] = [
			#'-topo',
		]


@TaskGen.feature('synopsys_dcshell')
@TaskGen.before('process_source')
def create_synopsys_dcshell_task(self):
	# get a node object for the main tcl script
	try:
		self.main_tcl_script = self.path.find_node(self.tcl_script)
	except AttributeError:
		Logs.error('You have to specify a the attribute \'tcl_script\' for feature "synopsys_dcshell".')
		return 1
	try:
		self.main_tcl_script.abspath()
	except AttributeError:
		Logs.error('In synopsys_dcshell: TCL script '+self.tcl_script+' not found.')
		return 1

	# convert source list to nodes
	self.sourcelist = self.to_nodes(getattr(self, 'source', []))
	# disable the process_source function
	self.source = []

	# create results output directory
	try:
		self.results_dir = self.get_or_create_results_dir()
	except Errors.WafError as e:
		Logs.error(e.msg)
		return 1

	# generate the node object for the sourcelist TCL script
	# this TCL script contains the commands to actually load the source files into dc_shell
	self.sourcelist_tcl_script = self.path.find_or_declare(self.name+'_source.tcl')
	os.environ['DC_SHELL_SOURCE_TCL'] = self.sourcelist_tcl_script.abspath()

	if not getattr(self,'verilog_sources',None):
		self.verilog_sources = []
	if not getattr(self,'systemverilog_sources',None):
		self.systemverilog_sources = []
	if not getattr(self,'vhdl_sources',None):
		self.vhdl_sources = []
	if not getattr(self,'other_sources',None):
		self.other_sources = []

	# divide sources into groups
	for f in self.sourcelist:
		fn = self.to_nodes(f)[0]

		if fn.suffix() == '.sv' or fn.suffix() == '.svh':
			self.systemverilog_sources.append(fn)
		elif fn.suffix() == '.v' or fn.suffix() == '.v':
			self.verilog_sources.append(fn)
		elif fn.suffix() == '.vhd' or fn.suffix() == '.vhdl':
			self.vhdl_source.append(fn)
		else:
			self.other_sources.append(fn)

	if len(self.other_sources) > 0:
		Logs.error('In synopsys_dcshell: There are unknown source files (at least there extensions indicate that).')
		return 1

	# write read statements for every source file into the source list TCL script
	f = open(self.sourcelist_tcl_script.abspath(),"w")
	for sourcefile in self.verilog_sources:
		f.write('analyze -format verilog '+sourcefile.abspath()+'\n')
	for sourcefile in self.vhdl_sources:
		f.write('analyze -format vhdl '+sourcefile.abspath()+'\n')
	for sourcefile in self.systemverilog_sources:
		f.write('analyze -format sverilog '+sourcefile.abspath()+'\n')
	f.close()

	# declare input list
	inputs = [self.main_tcl_script]
	inputs.extend(self.systemverilog_sources)
	inputs.extend(self.verilog_sources)
	inputs.extend(self.vhdl_sources)


	try:
		outputs = [self.get_synthesized_netlist_node()]
	except Errors.WafError as e:
		Logs.error(e.msg)
		return 1

	p = TclParser()
	p.input_file(self.main_tcl_script.abspath())
	#for cmd in p.parse():
	#	print cmd
	#	pass

	t = self.create_task('synopsysDcshellTask', inputs, outputs)

@TaskGen.taskgen_method
def get_or_create_results_dir(self):
	if not hasattr(self,'name'):
		raise Errors.WafError('In synopsys_dcshell: Please define the attribute \'name\' for this Task generator.')

	results_dir = self.bld.bldnode.make_node('results_'+self.name)
	results_dir.mkdir()

	if not results_dir.find_dir('results'):
		results_dir.make_node('results').mkdir()
	if not results_dir.find_dir('reports'):
		results_dir.make_node('reports').mkdir()

	return results_dir

@TaskGen.taskgen_method
def get_synthesized_netlist_node(self):
	if not hasattr(self,'design_name'):
		raise Errors.WafError('In synopsys_dcshell: Please define the attribute \'design_name\' for this Task generator.')

	return self.get_or_create_results_dir().find_dir('results').make_node(self.design_name+'.v')

class synopsysDcshellTask(Task.Task):
	vars = ['SYNOPSYS_DCSHELL','SYNOPSYS_DCSHELL_OPTIONS']

	def run(self):
		logfile = self.generator.get_logdir_node().make_node('dc_shell_'+self.generator.name+'.log')

		run_str = 'BRICK_RESULTS=%s %s %s -f %s -output_log_file %s' % (
				self.generator.results_dir.abspath(),
				self.env.SYNOPSYS_DCSHELL,
				" ".join(self.env.SYNOPSYS_DCSHELL_OPTIONS),
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
