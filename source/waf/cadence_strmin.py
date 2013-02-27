import os,re
from waflib import Task,Errors,Node,TaskGen,Configure,Node,Logs

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

	layout_node = self.get_cellview_path(cellview).make_node('layout.oa')


	try:
		getattr(self,'strmfile',None).abspath()
	except AttributeError:
		Logs.error("Stream file '"+getattr(self,'strmfile','')+"' not found.")
		return

	self.reflib_file = self.path.get_bld().make_node(os.path.join(self.path.bld_dir(),self.libname+'_'+self.cellname+'_streamin_reflib'))

	with open(self.reflib_file.abspath(),'w') as f:
		for lib in getattr(self,'reflibs',[]):
			f.write(lib+'\n')

	t = self.create_task('cdsStrminTask', self.strmfile, layout_node)


class cdsStrminTask(Task.Task):
	vars = ['CDS_STRMIN']

	def run(self):
		"""Checking logfile for critical warnings line by line"""

		run_str = '${CDS_STRMIN} -library '+self.generator.libname+' -topCell '+self.generator.cellname+' -view '+self.generator.viewname+' ${CDS_STRMIN_OPTIONS} -strmfile ${SRC[0].abspath()} -refLibList '+self.generator.reflib_file.abspath()
		run_str += ' -logFile '+self.env.BRICK_LOGFILES+'/'+self.generator.libname+'_'+self.generator.cellname+'_strmin.log'

		if hasattr(self.generator,'attach_tech_lib'):
			run_str += ' -attachTechFileOfLib '+self.generator.attach_tech_lib

		(f, dvars) = Task.compile_fun(run_str, False)
		return f(self)



# for convenience
@Configure.conf
def cds_strmin(bld,*k,**kw):
	set_features(kw,'cds_strmin')
	return bld(*k,**kw)

# vim: noexpandtab
