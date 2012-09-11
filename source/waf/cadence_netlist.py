import os
from waflib import Task,Errors,Node,TaskGen,Configure

def configure(conf):
	pass

class cdsNetlistTask(Task.Task):

	def run(self):
		split_path = Node.split_path(self.inputs[0].abspath())
		split_path.reverse()
		lib = split_path[3]
		cell = split_path[2]
		view = split_path[1]

		cmd = 'amsdesigner -lib %s -cell %s -view %s -compile all -netlist all -rundir . -ncvlogopt "-use5x -64bit"' % (lib,cell,view)
		return self.exec_command(cmd)

	#def runnable_status(self):
	#    pass

@TaskGen.feature('cds_netlist')
def add_cds_netlist_target(self):
	try:
		(lib,cell) = self.toplevel.split('.',2)
		(cell,view) = cell.split(':',2)
		config_file = self.path.find_dir(self.env['CDS_LIBS'][lib])
		if not config_file:
			raise Errors.ConfigurationError('Library '+lib+' in '+selv.env['CDS_LIBS'][lib]+' not found')
		config_file = config_file.find_resource(cell+'/'+view+'/expand.cfg')
		if not config_file:
			raise Errors.ConfigurationError('Cellview '+cell+':'+view+' in library '+lib+' not found.')

		t = self.create_task('cdsNetlistTask', config_file)
	except ValueError:
		raise Errors.ConfigurationError('For feature "cds_netlist", you need to specify a parameter "toplevel" in the form of lib.cell:view') 

# for convenience
@Configure.conf
def cds_netlist(bld,*k,**kw):
	set_features(kw,'cds_netlist')
	return bld(*k,**kw)


