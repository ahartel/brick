import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node

def configure(conf):
	conf.load('brick_general')

	"""This function gets called by waf upon loading of this module in a configure method"""
	if not conf.env.LOGFILES:
		conf.env.LOGFILES = './'
	conf.env['PLANAHEAD'] = 'planAhead'

@TaskGen.feature('planAhead')
def scan_planAhead_script(self):
	self.tcl_file_node = self.path.find_node(getattr(self,'tcl_file',None))
	if not self.tcl_file_node:
		raise Errors.ConfigurationError('A TCL file for planAhread could not be found: '+getattr(self,'tcl_file',None))

	inputs = [self.tcl_file_node]
	outputs = []
	variables = {}

	#
	# Project file parsing
	#
	with open(self.tcl_file_node.abspath(),'r') as tcl_handle:
		# This is ugly and will break!
		for line in tcl_handle:
			# skip comments
			if re.match('\s*#',line):
				continue

			# replace env variables
			get_env = re.search('\$env\s*\(\s*(\w+)\s*\)\s*',line)
			if get_env:
				line = re.sub('\$env\s*\(\w+\s*\)\s*',self.env[get_env.group(1)],line)

			# replace variables
			get_vars = re.search('\$(\w+)',line)
			while get_vars:
				line = re.sub('\$'+get_vars.group(1),variables[get_vars.group(1)],line)
				get_vars = re.search('\$(\w+)',line)

			# add the implicit dependencies
			m0 = re.search('add_files',line)
			if m0:
				# remove options
				line = re.sub('-norecurse\s+','',line)
				line = re.sub('-quiet\s+','',line)
				line = re.sub('-scan_for_includes\s+','',line)
				line = re.sub('-verbose\s+','',line)
				line = re.sub('-fileset\s+?.+?\s+?','',line)

				m1 = re.search('add_files\s+{(.+)}',line)
				if m1:
					files = m1.group(1).split(' ')
					for file in files:
						if self.env['BRICK_RESULTS'] in file:
							input_node = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),file))
							inputs.append(input_node)
						else:
							input_node = self.path.make_node(file)
							if input_node:
								inputs.append(input_node)
							else:
								raise Errors.ConfigurationError('File '+file+' not found in project file for planAhead project.')
				else:
					m2 = re.search('add_files\s+(.+)',line)
					if m2:
						file = m2.group(1)
						if self.env['BRICK_RESULTS'] in file:
							input_node = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),file))
							inputs.append(input_node)
						else:
							input_node = self.path.make_node(file)
							if input_node:
								inputs.append(input_node)
							else:
								raise Errors.ConfigurationError('File '+file+' not found in project file for planAhead project.')

			# look for variables
			m3 = re.search('set\s+(.+?)\s+(.+)',line)
			if m3:
				m3_1 = re.search('\[\s*\$env\s+(.+)\s*\]',m3.group(2))
				if m3_1:
					variables[m3.group(1)] = self.env[m3_1.group(1)]
				else:
					variables[m3.group(1)] = m3.group(2)

			# find out project dir and project name
			m4 = re.search('create_project',line)
			if m4:
				line = re.sub('-force\s+','',line)
				line = re.sub('-part\s+?.+?\s+?','',line)
				m5 = re.search('create_project\s+?([\.\-_\/\w]+)\s+?([\.\-_\/\w]+)',line)
				if m5:
					self.project_name = m5.group(1)
					self.project_dir = m5.group(2)
				else:
					raise Errors.ConfigurationError('Project name and/or project dir could not be inferred from TCL file '+self.tcl_file_node.abspath())

			# look for implemenatations
			m6 = re.search('launch_run\s+(\w+)',line)
			if m6:
				filename = os.path.join(self.project_dir,self.project_name+'.runs',m6.group(1),self.toplevel+'_routed.ncd')
				outputs.append(self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),filename)))

	outputs.append(outputs[0].parent.make_node(self.toplevel+'.pcf'))
	# save output file path to environment
	self.env['PLANAHEAD_OUTPUT'] = outputs[0].path_from(self.path)
	# create actual task
	self.planAheadTask = self.create_task('planAheadTask', inputs, outputs)

class planAheadTask(Task.Task):
	vars = ['PLANAHEAD']

	def run(self):
		"""Checking logfile for critical warnings line by line"""

		run_str = '${PLANAHEAD} -mode batch -source ${SRC[0].abspath()}'

		(f, dvars) = Task.compile_fun(run_str, False)
		return_value = f(self)

		found_error = 0
		with open(self.inputs[0].abspath(),'r') as logfile:
			pass
			# put critical warnings here

			#for line in logfile:
			#	# always_ff does not infer sequential logic
			#	m0 = re.match('@W: CL216',line)
			#	if m0:
			#		print line
			#		found_error = 1
			#	# always_comb does not infer combinatorial logic
			#	m0 = re.match('@W: CL217',line)
			#	if m0:
			#		print line
			#		found_error = 1
			#	# always_latch does not infer latch logic
			#	m0 = re.match('@W: CL218',line)
			#	if m0:
			#		print line
			#		found_error = 1

		return found_error


#@TaskGen.feature('planAhead')
#@TaskGen.after_method('scan_planAhead_script')
#def add_planAhead_target(self):
#
#	# generate synthesis task
#	t1 = self.create_task('planAheadTask', self.tcl_file_node)
#
#	# check logfile if not disabled by user
#	try:
#		self.check_logfile
#		if self.check_logfile == True:
#			t2 = self.create_task('synplifyCheckTask', t1.outputs[1])
#	except AttributeError:
#		t2 = self.create_task('synplifyCheckTask', t1.outputs[1])

# for convenience
@Configure.conf
def planAhead(bld,*k,**kw):
	set_features(kw,'planAhead')
	return bld(*k,**kw)


