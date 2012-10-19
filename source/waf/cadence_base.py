import os,re,copy
from waflib import Configure, TaskGen, Task

def configure(conf):
	# Here, we check if all the libraries given in CDS_LIBS
	# and all the include paths defined in CDS_LIB_INCLUDES
	# exist and merge them into CDS_LIBS_FLAT.
	conf.env['CDS_LIBS_FLAT'] = {}
	try:
		for key,value in conf.env['CDS_LIBS'].iteritems():
			conf.env['CDS_LIBS_FLAT'][key] = value
			if not conf.path.find_dir(value):
				conf.fatal('Cadence library '+key+' not found in '+value+'.')
	except AttributeError, e:
		conf.fatal('Please specify the environment variable CDS_LIBS before loading module \'cadence_base\'.')

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


class cdsWriteCdsLibs(Task.Task):
	def run(self):
		cdslib = open(self.outputs[0].abspath(),'w')
		libdefs = open(self.outputs[1].abspath(),'w')
		for key,value in self.env['CDS_LIBS'].iteritems():
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
