import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node

def configure(conf):
	conf.load('brick_general')

	"""This function gets called by waf upon loading of this module in a configure method"""
	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'
	conf.env['SYNPLIFY'] = 'synplify_premier_dp'

@TaskGen.feature('synplify')
def scan_synplify_project_file(self):
	"""This function extracts the output file and inputs files for synthesis from a synplify project (i.e. tcl) file."""

	self.project_file_node = self.path.find_node(getattr(self,'project_file',None))
	if not self.project_file_node:
		raise Errors.ConfigurationError('Project file for synplify not found: '+getattr(self,'project_file',''))
	# open the project file template
	input = open(self.project_file_node.abspath(),'r')
	inputs = [self.project_file_node]
	# split the filename into parts
	project_file_split = Node.split_path(self.project_file_node.abspath())
	# create the target project file
	self.project_file_node = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),project_file_split[len(project_file_split)-1]))
	output = open(self.project_file_node.abspath(),'w')
	variables = {}
	outputs = []
	for line in input:
		# copy file line by line
		output.write(line)
		# skip comments
		if re.match('\s*#',line):
			continue
		# replace env variables
		get_env = re.search('\[\s*get_env\s+(\w+)\s*\]',line)
		if get_env:
			if not get_env.group(1) in self.env:
				raise Errors.ConfigurationError('The environment variable '+get_env.group(1)+' used in synplify project file '+self.project_file_node.abspath()+' has not been defined.')

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
					print "Variable "+m0_1.group(1)+" not found in "+self.project_file

				outputs.append(self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),result_file)))
			else:
				# if the result path is given as a relative path,
				# synplify save the results relative to the project_file path,
				# not relative to the path where the program is executed in
				outputs.append(self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),m0.group(1))))


		# look for variables
		m3 = re.search('set\s+(.+?)\s+(.+)',line)
		if m3:
			m3_1 = re.search('\[\s*get_env\s+(.+)\s*\]',m3.group(2))
			if m3_1:
				variables[m3.group(1)] = self.env[m3_1.group(1)]
			else:
				variables[m3.group(1)] = m3.group(2)

	input.close()

	for file in getattr(self,'source_files',[]):
		node = self.path.find_node(file)
		if not node:
			raise Errors.ConfigurationError('File '+file+' not found in task ' + self.name)

		if node.suffix() == '.v':
			output.write('add_file -verilog "'+node.abspath()+'"\n')
		elif node.suffix() == '.sv' or node.suffix() == '.svh':
			output.write('add_file -verilog -vlog_std sysv "'+node.abspath()+'"\n')
		elif node.suffix() == '.sdc':
			output.write('add_file -constraint "'+node.abspath()+'"\n')
		else:
			raise Errors.ConfigurationError('Extension of file '+node.abspath()+' unknown.')

		inputs.append(node)

	for directory in getattr(self,'include_paths',[]):
		node = self.path.find_dir(directory)
		if not node:
			raise Errors.ConfigurationError('Include directory '+directory+' not found in synplify task.')

		output.write('set_option -include_path "'+node.abspath()+'"\n')

	output.close()

	self.logfile = outputs[0].change_ext('.srr')
	outputs.append(outputs[0].change_ext('.ncf'))
	outputs.append(outputs[0].parent.make_node('synplicity.ucf'))

	# generate synthesis task
	self.synplify_task = self.create_task('synplifyTask', inputs, outputs)

class synplifyTask(Task.Task):
	"""This task runs synplify with a project file and redirects it's STDOUT to a logfile"""
	vars = ['SYNPLIFY']

	def run(self):
		"""Checking logfile for critical warnings line by line"""

		logfile = self.env.BRICK_LOGFILES+'/'+Node.split_path(self.generator.project_file_node.abspath())[-1]

		run_str = '%s -batch %s -log %s' % (self.env.SYNPLIFY,self.generator.project_file_node.abspath(),logfile)

		out = ""
		try:
			out = self.generator.bld.cmd_and_log(run_str)#, quiet=Context.STDOUT)
		except Exception as e:
			out = e.stdout + e.stderr

		#(f, dvars) = Task.compile_fun(run_str, False)
		#return_value = f(self)

		#found_error = return_value
		found_error = 0
		errors = []
		with open(self.generator.logfile.abspath(),'r') as logfile_handle:
			for line in logfile_handle:
				# always_ff does not infer sequential logic
				if re.match("@W: CL216",line):
					errors.append(line)
					found_error = 1
				# always_comb does not infer combinatorial logic
				elif re.match("@W: CL217",line):
					errors.append(line)
					found_error = 1
				# always_latch does not infer latch logic
				elif re.match("@W: CL218",line):
					errors.append(line)
					found_error = 1
				# error
				elif re.match("@E:",line):
					errors.append(line)
					found_error = 1

		#if len(errors) > 0:
			#raise Errors.WafError("Found critical warning in logfile:\n"+"\n".join(errors))

		#return found_error
		return 0


# for convenience
@Configure.conf
def synplify(bld,*k,**kw):
	set_features(kw,'synplify')
	return bld(*k,**kw)

# vim: noexpandtab
