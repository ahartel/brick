import os
from waflib import Configure, TaskGen, Task

def configure(conf):
	pass

class cdsWriteCdsLibs(Task.Task):
	def run(self):
		cmd = 'cp %s %s' % (self.inputs[0].abspath(),self.outputs[0].abspath())
		return self.exec_command(cmd)


@TaskGen.feature("cds_write_libs")
def write_cds_lib(self):
	# write cds.lib file to toplevel directory
	cds_lib_path = self.path.make_node('cds.lib')
	cdslib = open(cds_lib_path.abspath(),'w')
	for key,value in self.env['CDS_LIBS'].iteritems():
		value = self.path.find_dir(value)
		cdslib.write('DEFINE '+key+' '+value.abspath()+"\n")
	cdslib.close()
	# create a copy task
	t = self.create_task('cdsWriteCdsLibs', cds_lib_path, self.target)
	# export cds.lib path
	self.env['CDS_LIB_PATH'] = self.target.abspath()

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

