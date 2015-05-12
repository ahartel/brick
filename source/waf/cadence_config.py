from waflib import Logs, TaskGen
from cadence_base import fix_verilog_name, fix_verilog_name_cellview

def configure(conf):
	pass

from waflib import Task
class CDSconfigTask(Task.Task):

	def run(self):
		cellname = fix_verilog_name(self.generator.cellname)
		with open(self.outputs[0].abspath(),'w') as expand_cfg:
			expand_cfg.write('//Revision 5\n')
			expand_cfg.write('config ' + cellname + ';\n')
			expand_cfg.write('design ' + self.generator.design + ';\n')
			expand_cfg.write('liblist ' + self.generator.liblist + ';\n')
			expand_cfg.write('\n')
			expand_cfg.write('viewlist '+self.generator.viewlist+';\n')
			expand_cfg.write('stoplist symbol;\n')
			expand_cfg.write('\n')
			expand_cfg.write(self.generator.mixins)
			expand_cfg.write('\n')
			expand_cfg.write('endconfig\n')

		with open(self.outputs[1].abspath(),'w') as master_tag:
			master_tag.write('-- Master.tag File, Rev:1.0\n')
			master_tag.write('expand.cfg\n')

		return 0

@TaskGen.feature('cds_config')
def gen_cds_config_task(self):
	# save libraries that are used for this configuration
	libs = getattr(self,'libs',[])
	# generate a comma seperated list of the libraries
	self.liblist = ''
	for lib in libs:
		# check if the library was defined in conf.env.CDS_LIBS
		if not self.env.CDS_LIBS_FLAT.has_key(lib):
			Logs.error('Cadence library '+lib+' was not defined in conf.env.CDS_LIBS_FLAT. Please specify a library path for this library in conf.env[\'CSD_LIBS\'].')
			return
		# add it to the string
		self.liblist += lib+', '
	# remove last comma
	self.liblist = self.liblist.rstrip(', ')
	# extract lib, cell and view
	(self.libname,self.cellname,self.viewname) = self.get_cadence_lib_cell_view_from_cellview()
	# save viewlist
	try:
		self.viewlist = ",".join(getattr(self,'viewlist',['schematic','symbol']))
	except TypeError:
		Logs.error('Please specify the viewlist as a list with the feature \'cds_config\'.')
		return
	# save top-level design
	self.design = fix_verilog_name_cellview(self.libname+'.'+self.cellname+':schematic')
	# mixins
	self.mixins = "\n".join(getattr(self,'mixins',[]))

	inputs = []
	if not hasattr(self,'config_cellview'):
		worklib_task = self.check_create_worklib_task(self.env.CDS_WORKLIB)
		if worklib_task:
			inputs = worklib_task.outputs

	config_libcellview = getattr(self,'config_cellview',self.env.CDS_WORKLIB+'.'+self.cellname+':brick_config')
	config_node = self.get_cellview_path(config_libcellview,True)

	self.create_task('CDSconfigTask',inputs,[config_node.make_node('expand.cfg'),config_node.make_node('master.tag')])

# vim: noexpandtab:

