import os
from waflib import Task,Errors,Node,TaskGen,Configure

def configure(conf):
	conf.env.AMSDESIGNER = 'amsdesigner'

class cdsNetlistTask(Task.Task):

	def run(self):
		"""Checking logfile for critical warnings line by line"""

		run_str = '${AMSDESIGNER} -lib '+self.generator.libname+' -cell '+self.generator.cellname+' -view '+self.generator.viewname+' -netlist all -compile all -rundir . -ncvlogopt -use5x -64bit'

		(f, dvars) = Task.compile_fun(run_str, False)
		return f(self)


#	def run(self):
#		split_path = Node.split_path(self.inputs[0].abspath())
#		split_path.reverse()
#		lib = split_path[3]
#		cell = split_path[2]
#		view = split_path[1]
#
#		cmd = 'amsdesigner -lib %s -cell %s -view %s -compile all -netlist all -rundir . -ncvlogopt "-use5x -64bit"' % (lib,cell,view)
#		return self.exec_command(cmd)
#
#	#def runnable_status(self):
#	#    pass

@TaskGen.feature('cds_netlist')
def add_cds_netlist_target(self):
	try:
		cellview = getattr(self,'view','')
		if cellview.find('.') == -1 or cellview.find(':') == -1:
			Logs.error('Please specify a cellview of the form Lib:Cell:View with the \'view\' attribute with the feature \'cds_netlist\'.')
			return
		(self.libname,rest) = cellview.split(".")
		(self.cellname,self.viewname) = rest.split(":")

		config_file = self.path.find_dir(self.env['CDS_LIBS_FLAT'][self.libname])
		if not config_file:
			raise Errors.ConfigurationError('Library '+lib+' in '+selv.env['CDS_LIBS_FLAT'][self.libname]+' not found')
		config_file = config_file.make_node(self.cellname+'/'+self.viewname+'/expand.cfg')
		#if not config_file:
		#	raise Errors.ConfigurationError('Cellview '+self.cellname+':'+self.viewname+' in library '+self.libname+' not found.')

		t = self.create_task('cdsNetlistTask', config_file)
	except ValueError:
		raise Errors.ConfigurationError('For feature "cds_netlist", you need to specify a parameter "toplevel" in the form of lib.cell:view')

# for convenience
@Configure.conf
def cds_netlist(bld,*k,**kw):
	set_features(kw,'cds_netlist')
	return bld(*k,**kw)


