import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs
from brick_general import ChattyBrickTask

def configure(conf):
	conf.load('brick_general')

	"""This function gets called by waf upon loading of this module in a configure method"""
	if not conf.env.BRICK_LOGFILES:
		conf.env.BRICK_LOGFILES = './logfiles'
	conf.env['CDS_STRMIN'] = 'strmin'
	conf.env['CDS_STRMIN_OPTIONS'] = [
			'-snapToGrid',
			'-case', 'preserve',
		]

@TaskGen.feature('cds_strmin')
def create_cds_strmin_task(self):
	cellview = getattr(self,'cellview','')

	if cellview.find('.') == -1 or cellview.find(':') == -1:
		Logs.error('Please specify a target cellview of the form Lib:Cell:View with the \'view\' attribute with the feature \'cds_strmin\'.')
		return
	(self.libname,rest) = cellview.split(".")
	(self.cellname,self.viewname) = rest.split(":")

	layout_node = self.get_cellview_path(cellview,True).make_node('layout.oa')

	try:
		getattr(self,'strmfile',None).abspath()
	except AttributeError:
		Logs.error("Stream file '"+getattr(self,'strmfile','')+"' not found.")
		return

	self.reflib_file = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.libname+'_'+self.cellname+'_streamin_reflib'))

	with open(self.reflib_file.abspath(),'w') as f:
		for lib in getattr(self,'reflibs',[]):
			f.write(lib+'\n')

	self.cellmap_file = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.libname+'_'+self.cellname+'_streamin_cellmap'))

	with open(self.cellmap_file.abspath(),'w') as f:
		for lib in getattr(self,'cellmap',[]):
			f.write(lib+'\n')


	t = self.create_task('cdsStrminTask', self.strmfile, layout_node)


@TaskGen.taskgen_method
def get_cds_strmin_logfile_node(self):
	return self.get_logdir_node().make_node(self.libname+'_'+self.cellname+'_strmin.log')

class cdsStrminTask(ChattyBrickTask):
	vars = ['CDS_STRMIN']
	run_str = '${CDS_STRMIN} -library ${gen.libname} -topCell ${gen.cellname} -view ${gen.viewname} ${CDS_STRMIN_OPTIONS} -strmfile ${SRC[0].abspath()} -refLibList ${gen.reflib_file.abspath()} -logfile ${gen.get_cds_strmin_logfile_node().abspath()} -cellMap ${gen.cellmap_file.abspath()}'

	def check_output(self,ret,out):
		for num,line in enumerate(out.split('\n')):
			if line.find('strmin:   ERROR:') == 0:
				Logs.error("Error in line %d: %s" % (num,line[16:]))
				ret = 1

		return ret


# for convenience
@Configure.conf
def cds_strmin(bld,*k,**kw):
	set_features(kw,'cds_strmin')
	return bld(*k,**kw)

# vim: noexpandtab
