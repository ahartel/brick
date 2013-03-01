import os,re,copy
from waflib import Configure, TaskGen, Task, Logs, Errors

def configure(conf):
	# Here, we check if all the libraries given in CDS_LIBS
	# and all the include paths defined in CDS_LIB_INCLUDES
	# exist and merge them into CDS_LIBS_FLAT.
	conf.env['CDS_LIBS_FLAT'] = {}
	found_absolute_path = False
	try:
		for key,value in conf.env['CDS_LIBS'].iteritems():
			conf.env['CDS_LIBS_FLAT'][key] = value
			if os.path.isabs(value):
				found_absolute_path = True
				if not conf.root.find_dir(value):
					conf.fatal('Cadence library '+key+' not found in '+value+'.')
			else:
				if not conf.path.find_dir(value):
					conf.fatal('Cadence library '+key+' not found in '+value+'.')
	except AttributeError, e:
		conf.fatal('Please specify the environment variable CDS_LIBS before loading module \'cadence_base\'.')

	if found_absolute_path:
		Logs.warn('Defining absolute paths in conf.env.CDS_LIBS can lead to undefined behavior, especially when doing so for your worklib!')

	try:
		my_includes = copy.copy(conf.env['CDS_LIB_INCLUDES'])
		include = my_includes.pop()
		while include:
			if not os.path.exists(os.path.expandvars(include)):
				conf.fatal('Cadence library include '+include+' does not exist.')
			else:
				with open(os.path.expandvars(include),'r') as include_file:
					for line in include_file.readlines():
						define = re.search('DEFINE\s+(\w+)\s+([\.\w\$\/]+)',line)
						if define:
							conf.env['CDS_LIBS_FLAT'][define.group(1)] = os.path.expandvars(define.group(2))
						else:
							inc = re.search('INCLUDE\s+([\.\w\$\/]+)',line)
							if inc:
								my_includes.append(inc.group(1))

			include = my_includes.pop()
	except AttributeError:
		pass
	except IndexError:
		pass

	if not conf.env.CDS_WORKLIB:
		conf.env.CDS_WORKLIB = 'worklib'
		worklib = conf.path.get_bld().make_node(os.path.join(conf.path.bld_dir(),'worklib'))
		if not os.path.isdir(worklib.abspath()):
			worklib.mkdir()

		if not conf.env['CDS_LIBS_FLAT'].has_key('worklib'):
			conf.env['CDS_LIBS']['worklib'] = worklib.path_from(conf.path)
			conf.env['CDS_LIBS_FLAT']['worklib'] = worklib.path_from(conf.path)

@TaskGen.taskgen_method
def get_cellview_path(self,libcellview,create_if_not_exists=False):
	# get an instance of the root node
	# ugly but hackalicious
	up = "../"
	for i in range(self.path.height()-1):
		up += "../"
	rootnode = self.path.find_dir(up)

	m0 = re.search('(\w+).(\w+):(\w+)', libcellview)
	if m0:
		lib = m0.group(1)
		cell = m0.group(2)
		view = m0.group(3)
		if not self.env.CDS_LIBS_FLAT:
			Logs.error('Please specify the environment variable CDS_LIBS and make sure to include module cadence_base.')
			return
		try:
			return_path = None
			if os.path.isabs(self.env.CDS_LIBS_FLAT[lib]):
				return_path = rootnode.find_dir(self.env.CDS_LIBS_FLAT[lib]+'/'+cell+'/'+view+'/')
			else:
				return_path = self.path.find_dir(self.env.CDS_LIBS_FLAT[lib]+'/'+cell+'/'+view+'/')

			if not return_path:
				print create_if_not_exists
				if create_if_not_exists:
					Logs.warn('Path for cellview \''+libcellview+'\' not found, creating it.')
					if os.path.isabs(self.env.CDS_LIBS_FLAT[lib]):
						return_path = self.rootnode.make_node(self.env.CDS_LIBS_FLAT[lib]+'/'+cell+'/'+view+'/')
						return_path.mkdir()
					else:
						return_path = self.path.make_node(self.env.CDS_LIBS_FLAT[lib]+'/'+cell+'/'+view+'/')
						return_path.mkdir()
				else:
					raise Errors.WafError('Path for cellview \''+libcellview+'\' not found in cadence_base.py')

			return return_path

		except TypeError:
			Logs.error('Please specify the environment variable CDS_LIBS and make sure to include module cadence_base.')


class cdsWriteCdsLibs(Task.Task):
	def run(self):
		cdslib = open(self.outputs[0].abspath(),'w')
		libdefs = open(self.outputs[1].abspath(),'w')
		for key,value in self.env['CDS_LIBS'].iteritems():
			if os.path.isabs(value):
				cdslib.write('DEFINE '+key+' '+value+"\n")
				libdefs.write('DEFINE '+key+' '+value+"\n")
			else:
				value = self.generator.path.find_dir(value)
				cdslib.write('DEFINE '+key+' '+value.abspath()+"\n")
				libdefs.write('DEFINE '+key+' '+value.abspath()+"\n")

		for value in self.env['CDS_LIB_INCLUDES']:
			cdslib.write('INCLUDE '+value+"\n")
			libdefs.write('INCLUDE '+value+"\n")

		cdslib.close()
		libdefs.close()

		hdlvar = open(self.outputs[2].abspath(),'w')
		hdlvar.write('DEFINE WORK worklib')
		hdlvar.close()

		return 0

@TaskGen.feature("cds_write_libs")
def write_cds_lib(self):
	# write cds.lib file to toplevel directory
	cds_lib_path = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'cds.lib'))
	lib_defs_path = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'lib.defs'))
	hdl_var_path = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),'hdl.var'))

	# create a copy task
	t = self.create_task('cdsWriteCdsLibs', None, [cds_lib_path, lib_defs_path, hdl_var_path])
	# export cds.lib path
	#self.env['CDS_LIB_PATH'] = self.target.abspath()

@Configure.conf
def check_cds_libs(self,*k,**kw):
	self.env['CDS_LIBS'] = {}
	for key,value in kw.iteritems():
		if type(value) == type('str'):
			# DEFINE
			if os.path.isdir(value):
				libpath = self.path.find_dir(value)
				self.env['CDS_LIBS'][key] = libpath.path_from(self.path)
			else:
				self.fatal('Directory '+value+' not found.')
		elif type(value) == type([]):
			# INCLUDE
			# TODO: implement
			pass

# vim: noexpandtab
