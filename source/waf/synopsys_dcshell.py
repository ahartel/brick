import os,re
from waflib import Task,Errors,TaskGen,Configure,Node,Logs
from TclParser import *

def configure(conf):
	"""This function gets called by waf upon loading of this module in a configure method"""

	conf.load('brick_general')

	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'
	conf.env['SYNOPSYS_DCSHELL'] = 'dc_shell'
	conf.env['SYNOPSYS_DCSHELL_OPTIONS'] = [
			#'-topo',
		]



@TaskGen.feature('synopsys_dcshell')
def create_synopsys_dcshell_task(self):
	# assemble file names for tcl scripts
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

	self.sourcelist = getattr(self,'sourcelist',[])

	# generate the path for the sourcelist TCL script
	self.sourcelist_tcl_script = self.path.get_bld()
	self.sourcelist_tcl_script.mkdir()
	self.sourcelist_tcl_script = self.sourcelist_tcl_script.make_node('dc_shell_'+getattr(self,'name','noname')+'source.tcl')
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
			self.other_source.append(fn)

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
	inputs.extend(self.other_sources)

	# check for existance of results dir
	# the actual results dir is a subdirectory of BRICK_RESULTS
	# called dc_shell_$DESIGN_NAME
	#self.results_dir = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.env.BRICK_RESULTS))
	#if not self.results_dir.find_dir('dc_shell_'+self.name):
	#	self.results_dir = self.results_dir.make_node('dc_shell_'+self.name)
	#	self.results_dir.mkdir()
	#else:
	#	self.results_dir = self.results_dir.make_node('dc_shell_'+self.name)
	#if not self.results_dir.find_dir('results'):
	#	self.results_dir.make_node('results').mkdir()
	#if not self.results_dir.find_dir('reports'):
	#	self.results_dir.make_node('reports').mkdir()

	#output_netlist = self.results_dir.find_node('results').make_node(self.toplevel+'.v')
	#output_sdc_file = self.results_dir.find_node('results').make_node(self.toplevel+'.sdc')

	#constraints_file = '0'
	#if hasattr(self,'constraints_file'):
	#	try:
	#		constraints_file = '"'+getattr(self,'constraints_file','').abspath()+'"'
	#		inputs.append(self.constraints_file)
	#	except AttributeError:
	#		Logs.error('You have given an undefined node object as constraints_file for feature "synopsys_dcshell".')

	## compile_ultra options
	#compile_ultra_options = ['-gate_clock']
	#if hasattr(self,'compile_high_effort') and self.compile_high_effort == True:
	#	compile_ultra_options.append('-timing_high_effort_script')

	## load extra package with tcl templates
	#from synopsys_dcshell_tcl import dc_shell_setup_tcl, dc_shell_main_tcl
	## write main tcl script
	#f = open(self.main_tcl_script.abspath(),"w")
	#f.write(dc_shell_main_tcl % (
	#			self.sourcelist_tcl_script.abspath(),
	#			self.setup_tcl_script.abspath(),
	#			'{'+' '.join([x.abspath() for x in getattr(self,'search_paths',[])])+'}',
	#			getattr(self,'max_cores','4'),
	#			constraints_file,
	#			'0', # compile_ultra -scan
	#			' '.join(compile_ultra_options)))
	#f.close()

	## Additional libraries
	#self.lib_search_paths = ''
	##if hasattr(self,'library_search_paths'):
	##	self.lib_search_paths = '"' + '" \\\n'.join([x.abspath() for x in getattr(self,'library_search_paths',[])]) + '" \\'

	#self.additional_libs = ''
	#if hasattr(self,'additional_library_files'):
	#	for lib_file in self.additional_library_files:
	#		(trunk,filename) = os.path.split(lib_file.abspath())

	#		self.additional_libs += '"'+filename+'" \\\n'
	#		self.lib_search_paths += '"'+trunk+'" \\\n'

	## write setup tcl script (containing mostly process specific data)
	## the only variable input here is the DESIGN_NAME a.k.a. self.toplevel
	#f = open(self.setup_tcl_script.abspath(),"w")
	#f.write(dc_shell_setup_tcl[getattr(self,'process','default')] % (self.toplevel,self.lib_search_paths,self.additional_libs))
	#f.close()

	## write out the source list
	#f = open(self.sourcelist_tcl_script.abspath(),"w")
	#try:
	#	sourcelist_string = "set systemverilog_source_list [list \\\n"+" \\\n".join([x.abspath() for x in self.systemverilog_sources])+" \\\n]\n\n"
	#	sourcelist_string += "set verilog_source_list [list \\\n"+" \\\n".join([x.abspath() for x in self.verilog_sources])+" \\\n]\n\n"
	#	sourcelist_string += "set vhdl_source_list [list \\\n"+" \\\n".join([x.abspath() for x in self.vhdl_sources])+" \\\n]\n\n"
	#except AttributeError:
	#	Logs.error('You have given an undefined node object as netlist for feature "synopsys_dcshell".')

	#f.write(sourcelist_string)
	#f.close()

	#inputs.extend(self.systemverilog_sources)
	#inputs.extend(self.verilog_sources)
	#inputs.extend(self.additional_library_files)

	self.results_dir = self.path.get_bld()
	if not self.results_dir.find_node('dc_shell_'+self.name):
		self.results_dir = self.results_dir.make_node('dc_shell_'+self.name)
		self.results_dir.mkdir()
	else:
		self.results_dir = self.results_dir.find_node('dc_shell_'+self.name)

	if not self.results_dir.find_dir('results'):
		self.results_dir.make_node('results').mkdir()
	if not self.results_dir.find_dir('reports'):
		self.results_dir.make_node('reports').mkdir()

	outputs = getattr(self,'outputs',[self.results_dir.find_dir('results').make_node(self.name+'.v')])

	p = TclParser()
	p.input_file(self.main_tcl_script.abspath())
	#for cmd in p.parse():
	#	print cmd
	#	pass

	t = self.create_task('synopsysDcshellTask', inputs, outputs)


class synopsysDcshellTask(Task.Task):
	vars = ['SYNOPSYS_DCSHELL','SYNOPSYS_DCSHELL_OPTIONS']

	def run(self):
		logfile = self.generator.path.get_bld().make_node('dc_shell_'+self.generator.name+'.log')

		run_str = 'BRICK_RESULTS=%s %s %s -f %s -output_log_file %s' % (self.generator.path.get_bld().abspath(), self.env.SYNOPSYS_DCSHELL, " ".join(self.env.SYNOPSYS_DCSHELL_OPTIONS), self.generator.main_tcl_script.abspath(),logfile.abspath())
		out = ""
		try:
			out = self.generator.bld.cmd_and_log(run_str,shell=True)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout + e.stderr

		#f = open(logfile.abspath(),'w')
		#f.write(out)
		#f.close()

		return 0

# vim: noexpandtab:
