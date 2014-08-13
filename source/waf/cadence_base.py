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
		conf.msg('Checking for environment variable CDS_LIBS','Found '+str(len(conf.env['CDS_LIBS_FLAT']))+' libraries.')
	except AttributeError, e:
		conf.msg('Checking for environment variable CDS_LIBS','None')

	if found_absolute_path:
		Logs.warn('Defining absolute paths in conf.env.CDS_LIBS can lead to undefined behavior, especially when doing so for your worklib!')

	try:
		# copy cds_includes
		my_includes = copy.copy(conf.env['CDS_LIB_INCLUDES'])
		# start processing stack
		include = my_includes.pop()
		while include:
			if not os.path.exists(os.path.expandvars(include)):
				conf.fatal('Cadence library include '+include+' does not exist.')
			else:
				with open(os.path.expandvars(include),'r') as include_file:
					for line in include_file.readlines():
						if re.match(r"^\s*\#",line):
							continue
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

	# if CDS_LIBS has not been defined, define it
	if len(conf.env['CDS_LIBS']) == 0:
		conf.env['CDS_LIBS'] = {}

	if not conf.env.CDS_WORKLIB:
		conf.env.CDS_WORKLIB = 'worklib'
		worklib = conf.path.get_bld().make_node('worklib')
		if not os.path.isdir(worklib.abspath()):
			worklib.mkdir()

		if not conf.env['CDS_LIBS_FLAT'].has_key('worklib'):
			try:
				conf.env['CDS_LIBS']['worklib'] = worklib.path_from(conf.path)
			except TypeError:
				conf.env['CDS_LIBS'] = {}
				conf.env['CDS_LIBS']['worklib'] = worklib.path_from(conf.path)
			conf.env['CDS_LIBS_FLAT']['worklib'] = worklib.path_from(conf.path)
		elif not conf.env['CDS_LIBS'].has_key('worklib'):
			try:
				conf.env['CDS_LIBS']['worklib'] = worklib.path_from(conf.path)
			except TypeError:
				conf.env['CDS_LIBS'] = {}
				conf.env['CDS_LIBS']['worklib'] = worklib.path_from(conf.path)

	conf.env['CDS_LIB_PATH'] = conf.path.get_bld().make_node('cds.lib').abspath()
	conf.env['CDS_HDLVAR_PATH'] = conf.path.get_bld().make_node('hdl.var').abspath()

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

@TaskGen.taskgen_method
def get_cadence_lib_cell_view_from_cellview(self):
	lib = None
	cell = None
	view = None
	try:
		if self.cellview.find('.') == -1 or self.cellview.find(':') == -1:
			Logs.error('Please specify a cellview of the form Lib:Cell:View with the \'view\' attribute with the feature \'cds_strmout\'.')
			return
		(lib,rest) = self.cellview.split(".")
		(cell,view) = rest.split(":")

	except ValueError:
		Logs.Error('For feature "cds_strmout", you need to specify a parameter "cellview" in the form of lib.cell:view')
		return 1

	return (lib,cell,view)
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
			if os.path.isabs(os.path.expandvars(value)):
				cdslib.write('INCLUDE '+value+"\n")
				libdefs.write('INCLUDE '+value+"\n")
			else:
				path = self.generator.path.find_node(os.path.expandvars(value)).abspath()
				cdslib.write('INCLUDE '+path+"\n")
				libdefs.write('INCLUDE '+path+"\n")

		cdslib.close()
		libdefs.close()

		hdlvar = open(self.outputs[2].abspath(),'w')
		hdlvar.write('DEFINE WORK worklib')
		hdlvar.close()

		return 0

@TaskGen.feature("cds_write_libs")
def write_cds_lib(self):
	# write cds.lib file to toplevel directory
	cds_lib_path = self.path.get_bld().make_node('cds.lib')
	lib_defs_path = self.path.get_bld().make_node('lib.defs')
	hdl_var_path = self.path.get_bld().make_node('hdl.var')

	# create a copy task
	t = self.create_task('cdsWriteCdsLibs', None, [cds_lib_path, lib_defs_path, hdl_var_path])

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
