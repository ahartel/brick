import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node

def configure(conf):
	"""This function gets called by waf upon loading of this module in a configure method"""
	if not conf.env.LOGFILES:
		conf.env.LOGFILES = './'
	conf.env['SYNPLIFY'] = 'synplify_premier_dp'

@TaskGen.feature('synplify')
@TaskGen.after_method('add_synplify_target')
def scan_synplify_project_file(self):
	"""This function extracts the output file and inputs files for synthesis from a synplify project (i.e. tcl) file."""

	project_file = self.synplify_task.inputs[0]
	input = open(project_file.abspath(),'r')
	logfile = ''
	variables = {}
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
					print "Variable "+m0_1.group(1)+" not found in "+project_file.abspath()

				self.synplify_task.set_outputs(self.path.make_node(result_file))
			else:
				# if the result path is given as a relative path,
				# synplify save the results relative to the project_file path,
				# not relative to the path where the program is executed in
				self.synplify_task.set_outputs(self.path.make_node(m0.group(1)))

		# look for the verilog/vhdl input files
		m1 = re.search('add_file.+"(.+)"',line)
		if m1:
			self.synplify_task.set_inputs(project_file.parent.find_node(m1.group(1)))

		# look for variables
		m3 = re.search('set\s+(.+?)\s+(.+)',line)
		if m3:
			m3_1 = re.search('\[\s*get_env\s+(.+)\s*\]',m3.group(2))
			if m3_1:
				variables[m3.group(1)] = self.env[m3_1.group(1)]
			else:
				variables[m3.group(1)] = m3.group(2)

	input.close()

	project_file_name = Node.split_path(project_file.bld_base())
	project_file_name.reverse()
	logfile = self.synplify_task.outputs[0].parent.make_node(project_file_name[0]+'.srr')
	#self.synplify_task.set_outputs(logfile)

	## check logfile if not disabled by user
	#try:
	#	self.check_logfile
	#	if self.check_logfile == True:
	#		t2 = self.create_task('synplifyCheckTask', logfile)
	#except AttributeError:
	#	t2 = self.create_task('synplifyCheckTask', logfile)

class synplifyTask(Task.Task):
	"""This task runs synplify with a project file and redirects it's STDOUT to a logfile"""
	run_str = '${SYNPLIFY} -batch ${SRC[0].abspath()}'

class synplifyCheckTask(Task.Task):
	"""This task checks a synplify logfile for critical warnings"""
	color = 'ORANGE'

	def run(self):
		"""Checking logfile for critical warnings line by line"""
		found_error = 0
		logfile = open(self.inputs[0].abspath(),'r')
		for line in logfile:
			# always_ff does not infer sequential logic
			m0 = re.match('@W: CL216',line)
			if m0:
				print line
				found_error = 1
			# always_comb does not infer combinatorial logic
			m0 = re.match('@W: CL217',line)
			if m0:
				print line
				found_error = 1
			# always_latch does not infer latch logic
			m0 = re.match('@W: CL218',line)
			if m0:
				print line
				found_error = 1

		logfile.close()

		if found_error:
			return 1
		#else:
		#	return 0


@TaskGen.feature('synplify')
def add_synplify_target(self):
	"""Register feature for the TaskGenerators"""
	project_file = self.path.find_node(getattr(self,'project_file',None))
	if not project_file:
		raise Errors.ConfigurationError('Project file for synplify not found: '+project_file.abspath())

	# generate synthesis task
	self.synplify_task = self.create_task('synplifyTask', project_file)


# for convenience
@Configure.conf
def synplify(bld,*k,**kw):
	set_features(kw,'synplify')
	return bld(*k,**kw)


