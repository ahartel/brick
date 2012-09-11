import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node

def configure(conf):
	conf.load('brick_general')

	"""This function gets called by waf upon loading of this module in a configure method"""
	if not conf.env.LOGFILES:
		conf.env.LOGFILES = './'
	conf.env['SYNPLIFY'] = 'synplify_premier_dp'

@TaskGen.feature('synplify')
def scan_synplify_project_file(self):
	"""This function extracts the output file and inputs files for synthesis from a synplify project (i.e. tcl) file."""

	self.project_file_node = self.path.find_node(getattr(self,'project_file',None))
	if not self.project_file_node:
		raise Errors.ConfigurationError('Project file for synplify not found: '+getattr(self,'project_file',''))

	input = open(self.project_file_node.abspath(),'r')
	logfile = ''
	variables = {}
	inputs = [self.project_file_node]
	outputs = []
	for line in input:
		# skip comments
		if re.match('\s*#',line):
			continue
		# replace env variables
		get_env = re.search('\[\s*get_env\s+(\w+)\s*\]',line)
		if get_env:
			line = re.sub('\[\s*get_env\s+\w+\s*\]',self.env[get_env.group(1)],line)

		# keep the rest
		#  _
		#  |
		#  v
		#
		# look for the results file
		m0 = re.search('project\s+-result_file\s+"(.+)"',line)
		if m0:
			# check if the line contains a reference to a variable
			m0_1 = re.search('\$(\w+)',m0.group(1))
			if m0_1:
				try:
					result_file = re.sub('\$(\w+)',variables[m0_1.group(1)],m0.group(1))
				except KeyError:
					print "Variable "+m0_1.group(1)+" not found in "+self.project_file_node.abspath()

				outputs.append(self.path.make_node(result_file))
			else:
				# if the result path is given as a relative path,
				# synplify save the results relative to the project_file path,
				# not relative to the path where the program is executed in
				outputs.append(self.path.make_node(m0.group(1)))

		# look for the verilog/vhdl input files
		m1 = re.search('add_file.+"(.+)"',line)
		if m1:
			inputs.append(self.project_file_node.parent.find_node(m1.group(1)))

		# look for variables
		m3 = re.search('set\s+(.+?)\s+(.+)',line)
		if m3:
			m3_1 = re.search('\[\s*get_env\s+(.+)\s*\]',m3.group(2))
			if m3_1:
				variables[m3.group(1)] = self.env[m3_1.group(1)]
			else:
				variables[m3.group(1)] = m3.group(2)

	input.close()

	outputs.append(outputs[0].change_ext('.srr'))

	# generate synthesis task
	self.synplify_task = self.create_task('synplifyTask', inputs, outputs)

class synplifyTask(Task.Task):
	"""This task runs synplify with a project file and redirects it's STDOUT to a logfile"""
	vars = ['SYNPLIFY']

	def run(self):
		"""Checking logfile for critical warnings line by line"""

		run_str = '${SYNPLIFY} -batch ${SRC[0].abspath()}'

		(f, dvars) = Task.compile_fun(run_str, False)
		return_value = f(self)

		found_error = return_value
		with open(self.outputs[1].abspath(),'r') as logfile:
			for line in logfile:
				# always_ff does not infer sequential logic
				if re.match('@W: CL216',line):
					print line
					found_error = 1
				# always_comb does not infer combinatorial logic
				elif re.match('@W: CL217',line):
					print line
					found_error = 1
				# always_latch does not infer latch logic
				elif re.match('@W: CL218',line):
					print line
					found_error = 1

		return found_error


# for convenience
@Configure.conf
def synplify(bld,*k,**kw):
	set_features(kw,'synplify')
	return bld(*k,**kw)


