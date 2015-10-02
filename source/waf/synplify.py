import os,re
from brick_general import ChattyBrickTask
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

	result_file = None

	self.project_file_node = self.path.find_node(getattr(self,'project_file',None))
	if not self.project_file_node:
		raise Errors.ConfigurationError('Project file for synplify not found: '+getattr(self,'project_file',''))

	# help file
	project_file_name = os.path.split(self.project_file_node.abspath())[1]
	help_file = self.bld.bldnode.make_node('brick_'+project_file_name)
	with open(help_file.abspath(),'w') as hf:
		hf.write('set results_dir ./results')

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

				outputs.append(self.bld.bldnode.make_node(result_file))
			else:
				# if the result path is given as a relative path,
				# synplify save the results relative to the project_file path,
				# not relative to the path where the program is executed in
				outputs.append(self.bld.bldnode.make_node(m0.group(1)))


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
		elif node.suffix() == '.vhd' or node.suffix() == '.vhdl':
			output.write('add_file -vhdl "'+node.abspath()+'"\n')
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

	self.logfile = self.env.BRICK_LOGFILES+'/'+Node.split_path(self.project_file_node.abspath())[-1]

	# generate synthesis task
	self.synplify_task = self.create_task('synplifyTask', inputs, outputs)

class synplifyTask(ChattyBrickTask):
	"""This task runs synplify with a project file and redirects it's STDOUT to a logfile"""
	vars = ['SYNPLIFY']
	run_str = '${SYNPLIFY} -batch ${gen.project_file_node.abspath()} -log ${gen.logfile}'

	def check_output(self,ret,out):
		#found_error = return_value
		found_error = 0
		errors = []
		for num,line in enumerate(out.split('\n')):
			for line in out:
				# always_ff does not infer sequential logic
				if re.match("@W: CL216",line):
					errors.append(line)
					# found_error = 1
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

		ret = ret | (found_error>0)
		return ret


# for convenience
@Configure.conf
def synplify(bld,*k,**kw):
	set_features(kw,'synplify')
	return bld(*k,**kw)

# vim: noexpandtab
