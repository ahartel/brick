from waflib import Logs

def configure(conf):
	pass

from waflib import Task
class CDSconfigTask(Task.Task):

	def run(self):
		with open(self.outputs[0].abspath(),'w') as expand_cfg:
			expand_cfg.write('//Revision 5\n')
			expand_cfg.write('config ' + self.generator.cellname + ';\n')
			expand_cfg.write('design ' + self.generator.libname + '.' + self.generator.cellname + ':schematic;\n')
			expand_cfg.write('liblist ' + self.generator.liblist + ';\n')
			expand_cfg.write('\n')
			expand_cfg.write('viewlist schematic, symbol;\n')
			expand_cfg.write('stoplist symbol;\n')
			expand_cfg.write('\n')
			expand_cfg.write('endconfig\n')

		with open(self.outputs[1].abspath(),'w') as master_tag:
			master_tag.write('-- Master.tag File, Rev:1.0\n')
			master_tag.write('expand.cfg\n')

		return 0

from waflib import TaskGen
@TaskGen.feature('cds_config')
def gen_cds_config_task(self):
	# save libraries that are used for this configuration
	libs = getattr(self,'libs',[])
	# generate a comma seperated list of the libraries
	self.liblist = ''
	for lib in libs:
		# check if the library was defined in conf.env.CDS_LIBS
		if not self.env.CDS_LIBS_FLAT.has_key(lib):
			Logs.error('Cadence library '+lib+' was not defined in conf.env.CDS_LIBS_FLAT')
			return
		# add it to the string
		self.liblist += lib+', '
	# remove last comma
	self.liblist = self.liblist.rstrip(',')

	cellview = getattr(self,'view','')
	if cellview.find('.') == -1 or cellview.find(':') == -1:
		Logs.error('Please specify a cellview of the form Lib:Cell:View with the \'view\' attribute with the feature \'cds_config\'.')
		return
	(self.libname,rest) = cellview.split(".")
	(self.cellname,self.viewname) = rest.split(":")

	config_node = None
	try:
		config_node = self.path.find_node(self.env['CDS_LIBS_FLAT'][self.libname])
		if not config_node.find_node(self.cellname+'/'+self.viewname):
			config_node = config_node.make_node(self.cellname+'/'+self.viewname)
			config_node.mkdir()
		else:
			config_node = config_node.find_node(self.cellname+'/'+self.viewname)

	except KeyError,e:
		Logs.error('Cadence library '+self.libname+' was not defined in conf.env.CDS_LIBS_FLAT')
		return

	self.create_task('CDSconfigTask',None,[config_node.make_node('expand.cfg'),config_node.make_node('master.tag')])



